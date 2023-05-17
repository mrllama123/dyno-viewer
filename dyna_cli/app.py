from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
)
from textual.reactive import reactive
from dyna_cli.app_workers import (
    update_dyn_table_info,
    dyn_table_query,
    UpdateDynDataTable,
)
from dyna_cli.aws.session import get_available_profiles
from dyna_cli.aws.ddb import scan_items, get_ddb_client, get_table_client, query_items
from dyna_cli.components.screens import (
    ProfileSelectScreen,
    RegionSelectScreen,
    TableSelectScreen,
    QueryScreen,
)
from dyna_cli.components.table import DataDynTable
from textual.worker import get_current_worker
from textual import work
from textual import log


from dyna_cli.components.types import TableInfo


class DynCli(App):
    BINDINGS = [
        ("x", "exit", "Exit"),
        ("p", "push_screen('profile')", "Profile"),
        ("t", "push_screen('tableSelect')", "Table"),
        ("r", "push_screen('regionSelect')", "Region"),
        ("q", "push_screen('query')", "Query"),
    ]
    SCREENS = {
        "tableSelect": TableSelectScreen(),
        "regionSelect": RegionSelectScreen(),
        "profile": ProfileSelectScreen(),
        "query": QueryScreen(),
    }

    CSS_PATH = ["components/css/query.css"]

    profiles = reactive(get_available_profiles())

    aws_profile = reactive("default")

    table_name = reactive("")

    aws_region = reactive("ap-southeast-2")

    dyn_query_params = reactive({})

    table_client = reactive(None)

    dyn_client = reactive(get_ddb_client())

    table_info = reactive(None)

    def compose(self) -> ComposeResult:
        yield DataDynTable()
        yield Footer()

    def update_table_client(self):
        if self.table_name != "":
            self.table_client = get_table_client(
                self.table_name, self.aws_region, self.aws_profile
            )

    def set_pagination_token(self, next_token: str | None) -> None:
        if next_token:
            self.dyn_query_params["ExclusiveStartKey"] = next_token
        else:
            self.dyn_query_params.pop("ExclusiveStartKey", None)

    # on methods

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

        self.dyn_client = get_ddb_client(
            region_name=self.aws_region, profile_name=self.aws_profile
        )
        self.update_table_client()

    async def on_query_screen_run_query(self, run_query: QueryScreen.RunQuery) -> None:
        params = {"KeyConditionExpression": run_query.key_cond_exp}
        if run_query.filter_cond_exp:
            params["FilterExpression"] = run_query.filter_cond_exp
        self.dyn_table_query = params
        dyn_table_query(self)

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

    # watcher methods

    async def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        if new_table_client:
            update_dyn_table_info(self)
            dyn_table_query(self)

    def watch_dyn_client(self, new_dyn_client):
        with self.SCREENS["tableSelect"].prevent(TableSelectScreen.TableName):
            self.SCREENS["tableSelect"].dyn_client = new_dyn_client

    def watch_table_info(self, new_table_info: TableInfo) -> None:
        with self.SCREENS["query"].prevent(QueryScreen.RunQuery):
            self.SCREENS["query"].table_info = new_table_info


def main() -> None:
    app = DynCli()
    app.run()


if __name__ == "__main__":
    main()
