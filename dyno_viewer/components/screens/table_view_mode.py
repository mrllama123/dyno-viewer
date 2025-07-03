from textual import log, on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer
from textual.worker import get_current_worker

from dyno_viewer.app_types import TableInfo
from dyno_viewer.aws.ddb import (
    query_items,
    scan_items,
    table_client_exist,
)
from dyno_viewer.components.screens import (
    QueryScreen,
    TableSelectScreen,
)
from dyno_viewer.components.table import DataTableManager


class QueryResult(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


class UpdateDynTableInfo(Message):
    def __init__(self, table_info: TableInfo) -> None:
        self.table_info = table_info
        super().__init__()


class TableViewer(Screen):
    BINDINGS = [
        Binding("t", "select_table", "Select table", show=False),
        Binding("q", "query_table", "Query", show=False),
    ]

    table_info = reactive(None)

    table_name = reactive("")

    dyn_query_params = reactive({})

    query_screen_parameters = reactive(None)

    # set always_update=True because otherwise textual thinks that the client hasn't changed when it actually has :(
    table_client = reactive(None, always_update=True)

    data = reactive([], always_update=True)

    def compose(self) -> ComposeResult:
        yield DataTableManager().data_bind(TableViewer.data, TableViewer.table_info)
        yield Footer()

    def update_table_client(self):
        if self.table_name:
            # Access app's profile and region
            app_profile = self.app.aws_profile
            app_region = self.app.aws_region
            log.info(
                f"updating table client for table {self.table_name} with profile {app_profile} in region {app_region}"
            )
            new_table_client = table_client_exist(
                self.table_name, app_region, app_profile
            )
            if new_table_client:
                self.table_client = new_table_client
            else:
                # If table doesn't exist in new profile/region, clear client and data
                self.table_client = None
                self.data = []
                self.table_info = None
                self.notify(
                    f"Table {self.table_name} not found in profile {app_profile} and region {app_region}",
                    severity="warning",
                )
                return  # exit early if table not found

            self.data = []
        else:
            self.table_client = None  # Clear client if no table name
            self.data = []
            self.table_info = None

    def set_pagination_token(self, next_token: str | None) -> None:
        if next_token:
            self.dyn_query_params["ExclusiveStartKey"] = next_token
        else:
            self.dyn_query_params.pop("ExclusiveStartKey", None)

    # worker methods

    @work(exclusive=True, group="update_dyn_table_info", thread=True)
    def get_dyn_table_info(self) -> None:
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.log("updating table info")
            self.log("key schema=", self.table_client.key_schema)
            self.log("gsi schema=", self.table_client.global_secondary_indexes)
            main_keys = {
                ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                    "AttributeName"
                ]
                for key in self.table_client.key_schema
            }

            gsi_keys = {
                gsi["IndexName"]: {
                    ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                        "AttributeName"
                    ]
                    for key in gsi["KeySchema"]
                }
                for gsi in self.table_client.global_secondary_indexes or []
            }

            self.post_message(
                UpdateDynTableInfo(
                    {
                        "tableName": self.table_client.name,
                        "keySchema": main_keys,
                        "gsi": gsi_keys,
                    }
                )
            )

    @work(exclusive=True, group="dyn_table_query", thread=True)
    def run_table_query(self, dyn_query_params, update_existing=False):
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.log("dyn_params=", dyn_query_params)
            result, next_token = (
                query_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **dyn_query_params,
                )
                if "KeyConditionExpression" in dyn_query_params
                else scan_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **dyn_query_params,
                )
            )
            self.post_message(QueryResult(result, next_token, update_existing))

    # on methods

    # def on_mount(self) -> None:
    #     # need to do so that queries are persistent across screen changes
    #     self.app.install_screen(QueryScreen(), "query")

    @on(DataTableManager.PaginateRequest)
    async def paginate_table(self, _) -> None:
        table = self.query_one(DataTableManager)
        if "ExclusiveStartKey" in self.dyn_query_params:
            self.run_table_query(self.dyn_query_params, update_existing=True)
        else:
            table.loading = False

    @on(UpdateDynTableInfo)
    async def update_table_info(self, update: UpdateDynTableInfo) -> None:
        self.table_info = update.table_info
        query_screen = self.app.get_screen("query")
        query_screen.table_info = update.table_info

    async def run_query(self, run_query: QueryScreen.RunQuery) -> None:
        self.log.info(f"Running query on {self.table_name} with params: {run_query}")
        params = (
            {"KeyConditionExpression": run_query.key_cond_exp}
            if run_query.key_cond_exp
            else {}
        )

        if run_query.filter_cond_exp:
            params["FilterExpression"] = run_query.filter_cond_exp

        if run_query.index != "table":
            params["IndexName"] = run_query.index

        self.dyn_query_params = params
        self.log.info(f"Querying {self.table_name} with params: {params}")
        self.run_table_query(params)
        self.data = []

    @on(QueryResult)
    async def update_table(self, update_data: QueryResult) -> None:
        table = self.query_one(DataTableManager)
        self.data = self.data + [update_data.data]
        self.set_pagination_token(update_data.next_token)
        table.loading = False

    # action methods
    @work
    async def action_query_table(self) -> None:
        if self.table_client:
            self.app.push_screen("query")
        else:
            self.notify("No table selected")

    @work
    async def action_select_table(self) -> None:
        """Open the table select screen."""
        table = await self.app.push_screen_wait(TableSelectScreen())
        if table:
            self.table_name = table
            self.update_table_client()
        else:
            self.table_name = ""
            self.data = []

    async def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        if new_table_client:
            log.info("table client changed and table found, Update table data")
            self.get_dyn_table_info()

            self.run_table_query(self.dyn_query_params)
        else:
            log.info("table client changed and table not found, Clear table data")
            self.data = []
            self.table_info = None  # Clear table info as well
