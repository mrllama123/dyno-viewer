from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
)
from textual.reactive import reactive
from dyna_cli.aws.session import get_available_profiles
from dyna_cli.aws.ddb import scan_items, get_ddb_client, get_table_client
from dyna_cli.components.screens import ProfileSelectScreen, RegionSelectScreen, TableSelectScreen
from dyna_cli.components.table import DataDynTable



class DynCli(App):
    BINDINGS = [
        ("x", "exit", "Exit"),
        ("p", "push_screen('profile')", "Profile"),
        ("t", "push_screen('tableSelect')", "Table"),
        ("r", "push_screen('regionSelect')", "Region"),
    ]
    SCREENS = {
        "tableSelect": TableSelectScreen(),
        "regionSelect": RegionSelectScreen(),
        "profile": ProfileSelectScreen(),
    }

    profiles = reactive(get_available_profiles())

    aws_profile = reactive("default")

    table_name = reactive("")

    aws_region = reactive("ap-southeast-2")

    table_client = reactive(None)

    dyn_client = reactive(get_ddb_client())

    def compose(self) -> ComposeResult:
        yield Footer()
        yield DataDynTable()

    # on methods

    async def on_region_select_screen_region_selected(
        self, selected_region: RegionSelectScreen.RegionSelected
    ) -> None:
        self.aws_region = selected_region.region
        self.dyn_client = get_ddb_client(selected_region.region, self.aws_profile)

        self.table_client = get_table_client(
            self.table_name, selected_region.region, self.aws_profile
        )

    async def on_table_select_screen_table_name(
        self,
        new_table_name: TableSelectScreen.TableName,
    ) -> None:
        if self.table_name != new_table_name:
            self.table_name = new_table_name.table
            self.table_client = get_table_client(
                new_table_name.table, self.aws_region, self.aws_profile
            )

    async def on_profile_select_screen_profile_selected(
        self, selected_profile: ProfileSelectScreen.ProfileSelected
    ) -> None:
        self.aws_profile = selected_profile.profile
        self.dyn_client = get_ddb_client(selected_profile, self.aws_region)
        self.table_client = get_table_client(
            self.table_name, self.aws_region, selected_profile.profile
        )

    # action methods

    async def action_exit(self) -> None:
        self.app.exit()

    # watcher methods

    def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        table = self.query_one(DataDynTable)
        table.clear(columns=True)
        if new_table_client:
            # TODO make this more extendable i.e query's, gsi lookups
            results, next_token = scan_items(new_table_client, paginate=False, Limit=10)
            table.add_columns(results)
            table.add_rows(results)


def main() -> None:
    app = DynCli()
    app.run()


if __name__ == "__main__":
    main()
