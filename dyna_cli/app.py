from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
)
from textual.reactive import reactive
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
from botocore.exceptions import ClientError

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

    CSS_PATH = [
        "components/css/queryInput.css",
        "components/css/queryScreen.css",
        "components/css/filterQueryInput.css",
    ]

    profiles = reactive(get_available_profiles())

    aws_profile = reactive("default")

    table_name = reactive("")

    aws_region = reactive("ap-southeast-2")

    table_client = reactive(None)

    dyn_client = reactive(get_ddb_client())

    table_info = reactive(None)

    def compose(self) -> ComposeResult:
        yield Footer()
        yield DataDynTable()

    def update_table_client(self):
        if self.table_name != "":
            self.table_client = get_table_client(
                self.table_name, self.aws_region, self.aws_profile
            )

    @work(exclusive=True, group="full_update_data_table")
    def full_update_data_table(self, table_client, query_params=None) -> None:
        table = self.query_one(DataDynTable)
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(table.clear, columns=True)
            log("params=", query_params)
            results, next_token = (
                query_items(table_client, paginate=False, **query_params)
                if query_params
                else scan_items(table_client, paginate=False, Limit=20)
            )
            log(f"found {len(results)} items")
            if results:
                self.call_from_thread(table.refresh_data, self.table_info, results)
            else:
                self.call_from_thread(table.clear)

    @work(exclusive=True, group="update_dyn_table_info")
    def update_dyn_table_info(self):
        worker = get_current_worker()
        if not worker.is_cancelled:
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
                for gsi in self.table_client.global_secondary_indexes
            }

            def update(self, main_keys, gsi_keys):
                self.table_info = {"keySchema": main_keys, "gsi": gsi_keys}

            self.call_from_thread(update, self, main_keys, gsi_keys)

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
        self.full_update_data_table(self.table_client, params)

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
            self.full_update_data_table(new_table_client)
            self.update_dyn_table_info()

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
