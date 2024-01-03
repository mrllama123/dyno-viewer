from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
)
from textual.reactive import reactive
from dyno_viewer.aws.session import get_available_profiles
from dyno_viewer.aws.ddb import (
    get_ddb_client,
    query_items,
    scan_items,
    table_client_exist,
)
from dyno_viewer.components.screens import (
    ProfileSelectScreen,
    RegionSelectScreen,
    TableSelectScreen,
    QueryScreen,
    HelpMenu,
)
from dyno_viewer.components.table import DataDynTable
from textual.worker import get_current_worker
from textual.binding import Binding
from textual import work, log, on
import pyclip
from itertools import cycle
from dyno_viewer.app_types import TableInfo
from textual.message import Message
from dyno_viewer.util import output_to_csv_str
from dyno_viewer.util.util import format_output

cursors = cycle(["column", "row", "cell"])


class UpdateDynDataTable(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


class UpdateDynTableInfo(Message):
    def __init__(self, table_info: TableInfo) -> None:
        self.table_info = table_info
        super().__init__()


class DynCli(App):
    BINDINGS = [
        ("x", "exit", "Exit"),
        ("p", "push_screen('profile')", "Profile"),
        ("t", "push_screen('tableSelect')", "Table"),
        ("r", "push_screen('regionSelect')", "Region"),
        ("q", "push_screen_query", "Query"),
        ("?", "push_screen('help')", "help"),
        Binding("ctrl+c", "copy_table_data", "Copy", show=False),
        Binding("ctrl+r", "change_cursor_type", "Change Cursor type", show=False),
    ]
    SCREENS = {
        "tableSelect": TableSelectScreen(),
        "regionSelect": RegionSelectScreen(),
        "profile": ProfileSelectScreen(),
        "query": QueryScreen(),
        "help": HelpMenu(),
    }

    CSS_PATH = ["components/css/query.css", "components/css/table.css"]

    profiles = reactive(get_available_profiles())

    aws_profile = reactive(None)

    table_name = reactive("")

    aws_region = reactive("ap-southeast-2")

    dyn_query_params = reactive({})

    # set always_update=True because otherwise textual thinks that the client hasn't changed when it actually has :(
    table_client = reactive(None, always_update=True)

    dyn_client = reactive(get_ddb_client())

    table_info = reactive(None)

    def compose(self) -> ComposeResult:
        yield DataDynTable(id="dynDataTable")
        yield Footer()

    def update_table_client(self):
        if self.table_name != "":
            log.info(f"updating table client with profile {self.aws_profile}")
            new_table_client = table_client_exist(
                self.table_name, self.aws_region, self.aws_profile
            )
            if new_table_client:
                self.table_client = new_table_client
            else:
                table = self.query_one(DataDynTable)
                table.clear()

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
            # temp disable logging doesn't work
            # self.log(f"updating table info")
            # self.log("key schema=", self.table_client.key_schema)
            # self.log("gsi schema=", self.table_client.global_secondary_indexes)
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
                UpdateDynTableInfo({"keySchema": main_keys, "gsi": gsi_keys})
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

            self.post_message(UpdateDynDataTable(result, next_token, update_existing))

    # on methods

    def on_mount(self):
        table = self.query_one(DataDynTable)
        table.focus()

    @on(DataDynTable.CellHighlighted)
    async def paginate_dyn_data(
        self, highlighted: DataDynTable.CellHighlighted
    ) -> None:
        if highlighted.coordinate.row == highlighted.data_table.row_count - 1:
            if "ExclusiveStartKey" in self.dyn_query_params:
                log.info("adding more items")

                self.run_table_query(self.dyn_query_params, update_existing=True)

    @on(UpdateDynTableInfo)
    async def update_table_info(self, update: UpdateDynTableInfo) -> None:
        self.table_info = update.table_info

    async def on_region_select_screen_region_selected(
        self, selected_region: RegionSelectScreen.RegionSelected
    ) -> None:
        self.aws_region = selected_region.region
        self.dyn_client = get_ddb_client(selected_region.region, self.aws_profile)
        self.update_table_client()

    async def on_table_select_screen_table_name(
        self,
        new_table_name: TableSelectScreen.TableName,
    ) -> None:
        if self.table_name != new_table_name:
            self.table_name = new_table_name.table
            self.update_table_client()

    async def on_profile_select_screen_profile_selected(
        self, selected_profile: ProfileSelectScreen.ProfileSelected
    ) -> None:
        self.aws_profile = selected_profile.profile
        log.info(f"{self.aws_profile} profile selected")
        self.dyn_client = get_ddb_client(
            region_name=self.aws_region, profile_name=self.aws_profile
        )
        self.update_table_client()

    async def on_query_screen_run_query(self, run_query: QueryScreen.RunQuery) -> None:
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
        self.run_table_query(params)

    async def on_update_dyn_data_table(self, update_data: UpdateDynDataTable) -> None:
        table = self.query_one(DataDynTable)
        if update_data.update_existing_data:
            table.add_dyn_data_existing(update_data.data)
            self.set_pagination_token(update_data.next_token)
        else:
            table.add_dyn_data(self.table_info, update_data.data)
            self.set_pagination_token(update_data.next_token)

    # action methods

    async def action_exit(self) -> None:
        table = self.query_one(DataDynTable)
        # ensure we don't have any dirty data for next time app runs
        table.clear()
        self.app.exit()

    async def action_push_screen_query(self) -> None:
        if self.table_client:
            self.push_screen("query")
        else:
            self.notify("No table selected")

    async def action_copy_table_data(self) -> None:
        query_table = self.query(DataDynTable)
        if query_table:
            table = query_table[0]
            if table.row_count > 0:
                if table.cursor_type == "cell":
                    cell = table.get_cell_at(table.cursor_coordinate)
                    if cell is not None:
                        pyclip.copy(format_output(cell))
                elif table.cursor_type == "row":
                    row = table.get_row_at(table.cursor_row)
                    if row:
                        pyclip.copy(output_to_csv_str(row))
                elif table.cursor_type == "column":
                    col = table.get_column_at(table.cursor_column)
                    if col:
                        pyclip.copy(output_to_csv_str(col))

    async def action_change_cursor_type(self) -> None:
        query_table = self.query(DataDynTable)
        if query_table:
            table = query_table[0]
            next_cursor = next(cursors)
            self.notify(f"selection mode: {next_cursor}", timeout=1)
            table.cursor_type = next_cursor

    # watcher methods

    async def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        if new_table_client:
            log.info("table client changed and table found, Update table data")
            self.get_dyn_table_info()
            self.run_table_query(self.dyn_query_params)
        else:
            log.info("table client changed and table not found, Clear table data")
            self.query_one(DataDynTable).clear()

    def watch_dyn_client(self, new_dyn_client):
        with self.SCREENS["tableSelect"].prevent(TableSelectScreen.TableName):
            self.SCREENS["tableSelect"].dyn_client = new_dyn_client

    def watch_table_info(self, new_table_info: TableInfo) -> None:
        with self.SCREENS["query"].prevent(QueryScreen.RunQuery):
            self.SCREENS["query"].table_info = new_table_info


def run() -> None:
    app = DynCli()
    app.run()
