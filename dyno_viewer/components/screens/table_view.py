from textual import log, on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer
from textual.worker import get_current_worker

from dyno_viewer.aws.ddb import (
    get_ddb_client,
    query_items,
    scan_items,
    table_client_exist,
)
from dyno_viewer.components.screens import (
    TableSelectScreen,
)
from dyno_viewer.components.screens.file_chooser import SaveFileChooser
from dyno_viewer.components.screens.profile_select import ProfileSelectScreen
from dyno_viewer.components.screens.query import QueryScreen
from dyno_viewer.components.screens.query_history import QueryHistoryScreen
from dyno_viewer.components.screens.region_select import RegionSelectScreen
from dyno_viewer.components.screens.saved_querys import SavedQueriesScreen
from dyno_viewer.components.table import DataTableManager
from dyno_viewer.db.utils import add_query_history
from dyno_viewer.models import OutputFormat, QueryParameters, TableInfo
from dyno_viewer.util import save_query_results_to_csv, save_query_results_to_json


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
        Binding("q", "query_table", "Query table", show=False),
        Binding("o", "save_query", "Output query result to file", show=False),
        Binding("h", "show_query_history", "Show query history", show=False),
        Binding("y", "show_saved_queries", "Show saved queries", show=False),
        Binding(
            "p",
            "select_profile",
            "Profile",
            tooltip="Select AWS Profile",
        ),
        Binding("r", "select_region", "Region", tooltip="Select AWS Region"),
    ]
    HELP = """
    ## Table viewer 
    """

    table_info = reactive(None)

    table_name = reactive("")

    query_params: QueryParameters | None = reactive(None)

    draft_query_params: QueryParameters | None = reactive(None)

    aws_profile = reactive(None)
    aws_region = reactive("ap-southeast-2")
    dyn_client = reactive(
        get_ddb_client(region_name="ap-southeast-2", profile_name=None)
    )

    # set always_update=True because otherwise textual thinks that the client hasn't changed when it actually has :(
    table_client = reactive(None, always_update=True)

    data = reactive([], always_update=True)

    def compose(self) -> ComposeResult:
        yield DataTableManager().data_bind(TableViewer.data, TableViewer.table_info)
        yield Footer()

    def update_table_client(self):
        if self.table_name:
            # Access app's profile and region
            app_profile = self.aws_profile
            app_region = self.aws_region
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
    def run_table_query(self, query_params: QueryParameters, update_existing=False):
        worker = get_current_worker()
        if not worker.is_cancelled:
            extra_params = query_params.boto_params if query_params else {}
            result, next_token = (
                scan_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **extra_params,
                )
                if getattr(query_params, "scan_mode", True)
                else query_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **extra_params,
                )
            )
            self.log.info(f"query result: {result}")
            self.post_message(QueryResult(result, next_token, update_existing))

    # on methods

    @on(DataTableManager.PaginateRequest)
    async def paginate_table(self, _) -> None:
        table = self.query_one(DataTableManager)
        if not self.query_params:
            self.notify("No query parameters set, cannot paginate.")
            table.loading = False
            return

        if self.query_params.next_token:
            self.run_table_query(self.query_params, update_existing=True)
        else:
            table.loading = False

    @on(UpdateDynTableInfo)
    async def update_table_info(self, update: UpdateDynTableInfo) -> None:
        self.table_info = update.table_info

    @on(QueryResult)
    async def update_table(self, update_data: QueryResult) -> None:
        self.log.info(
            f"Received query result with {len(update_data.data)} items and next token: {update_data.next_token}"
        )
        table = self.query_one(DataTableManager)
        if update_data.update_existing_data:
            # If we are updating existing data, we should not clear the current data
            self.log.info("Updating existing data in the table")
            self.data = self.data + [update_data.data]
            table.increment_page_index()
        else:
            # If not updating existing data, clear the current data
            self.data = [update_data.data]

        # when scan
        if not self.query_params:
            self.query_params = QueryParameters(
                primary_key_name=self.table_info["keySchema"]["primaryKey"],
                sort_key_name=self.table_info["keySchema"]["sortKey"],
                next_token=update_data.next_token,
                scan_mode=True,
            )
        else:
            self.query_params.next_token = update_data.next_token
        table.loading = False

    # action methods
    @work
    async def action_select_profile(self) -> None:
        """Open the profile select screen."""
        profile = await self.app.push_screen_wait(ProfileSelectScreen())
        if profile:
            self.aws_profile = profile

    @work
    async def action_select_region(self) -> None:
        """Open the region select screen."""
        region = await self.app.push_screen_wait(RegionSelectScreen())
        if region:
            self.aws_region = region

    @work
    async def action_query_table(self) -> None:
        if not self.table_client:
            self.notify("No table selected", severity="warning")
            return
        new_query_param = await self.app.push_screen_wait(
            QueryScreen(self.table_info, self.draft_query_params or self.query_params)
        )
        if new_query_param.draft:
            self.draft_query_params = new_query_param
            return

        self.query_params = new_query_param
        self.draft_query_params = None
        await add_query_history(self.app.db_session, new_query_param)

    @work
    async def action_select_table(self) -> None:
        """Open the table select screen."""
        table = await self.app.push_screen_wait(TableSelectScreen(self.dyn_client))
        if table:
            self.table_name = table
            self.update_table_client()
        else:
            self.table_name = ""
            self.data = []

    @work
    async def action_save_query(self) -> None:
        """Open the save query screen."""
        if self.data:
            file_to_save = await self.app.push_screen_wait(SaveFileChooser())
            if file_to_save:
                try:
                    if file_to_save.file_format == OutputFormat.CSV:
                        save_query_results_to_csv(
                            file_to_save.path,
                            [item for page in self.data if page for item in page],
                        )
                    else:
                        save_query_results_to_json(
                            file_to_save.path,
                            [item for page in self.data if page for item in page],
                        )

                    self.notify(f"Query results saved to {file_to_save.path}")
                except Exception as e:  # pylint: disable=broad-except
                    self.log.error(f"Error saving query results: {e}")
                    self.notify(f"Error saving query results: {e}", severity="error")
        else:
            self.notify("Empty data, cannot save.")

    @work
    async def action_show_query_history(self) -> None:
        """Open the query history screen."""
        if self.table_client:
            new_query_param = await self.app.push_screen_wait(QueryHistoryScreen())
            if new_query_param:

                self.query_params = new_query_param

        else:
            self.notify("No table selected", severity="warning")

    @work
    async def action_show_saved_queries(self) -> None:
        """Open the saved queries screen."""
        if self.table_client:
            new_query_param = await self.app.push_screen_wait(SavedQueriesScreen())
            if new_query_param:
                query_screen = self.app.get_screen("query")
                self.query_params = new_query_param
                query_screen.input_query_params = new_query_param

        else:
            self.notify("No table selected", severity="warning")

    async def watch_aws_profile(self, new_profile: str | None) -> None:
        log.info(f"App: AWS Profile changed to: {new_profile}")
        self.dyn_client = get_ddb_client(
            region_name=self.aws_region, profile_name=new_profile
        )
        self.screen.update_table_client()

    async def watch_aws_region(self, new_region: str) -> None:
        log.info(f"App: AWS Region changed to: {new_region}")
        self.dyn_client = get_ddb_client(
            region_name=new_region, profile_name=self.aws_profile
        )
        self.screen.update_table_client()

    async def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        if new_table_client:
            log.info("table client changed and table found, Update table data")
            self.get_dyn_table_info()

            self.run_table_query(self.query_params)
        else:
            log.info("table client changed and table not found, Clear table data")
            self.data = []
            self.table_info = None  # Clear table info as well

    async def watch_query_params(self, new_query_params: QueryParameters) -> None:
        """Update the query parameters and run the query."""
        if self.table_client:
            log.info(f"Running query with params: {new_query_params}")
            self.run_table_query(new_query_params)
        else:
            log.warning("No table client available, cannot run query.")
