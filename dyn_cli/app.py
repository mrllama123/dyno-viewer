from pathlib import Path
from typing import Set

from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    MarkdownViewer,
    DataTable,
    ListItem,
    ListView,
    Label,
    Button,
    Static,
)
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.containers import Horizontal, Vertical
from textual.message import Message
from rich.text import Text, TextType
import textual.events as events
from dyn_cli.aws.session import get_available_profiles, get_all_regions
import boto3
import pandas as pd
from dyn_cli.aws.ddb import scan_items, get_ddb_client, get_table_client


class DynTable(Widget):
    data_table = pd.DataFrame()

    def compose(self) -> ComposeResult:
        yield DataTable()

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.data_table.columns.tolist())
        table.add_rows(self.data_table.values.tolist())

    def change_table_data(self, table_name, region, profile):
        dyn_table_client = get_table_client(table_name, region, profile)
        table = self.query_one(DataTable)
        results, next_token = scan_items(dyn_table_client, paginate=False, Limit=10)
        self.data_table = pd.DataFrame(results)

        table.clear()
        table.add_columns(*self.data_table.columns.tolist())
        table.add_rows(self.data_table.values.tolist())

    def clear_table(self):
        table = self.query_one(DataTable)
        table.clear()


class DataDynTable(DataTable):
    def add_columns(self, dyn_data: list[dict]) -> list[any]:
        cols = {attr for item in dyn_data for attr in item.keys()}
        return super().add_columns(*cols)

    def add_rows(self, dyn_data: list[dict]) -> list[any]:
        cols = [str(col.label) for col in self.columns.values()]
        rows = [[item.get(col) for col in cols] for item in dyn_data]
        return super().add_rows(rows)


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:
        dyn_client = get_ddb_client(region_name=self.parent.aws_region)
        dynamodb_tables = dyn_client.list_tables()["TableNames"]

        yield ListView(
            *[ListItem(Label(table), id=table) for table in dynamodb_tables],
            id="dynTablesSelect",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.TableName(selected.item.id))
        self.app.pop_screen()


class RegionSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class RegionSelected(Message):
        """"""

        def __init__(self, region: str) -> None:
            self.region = region
            super().__init__()

    def compose(self) -> ComposeResult:
        yield ListView(
            *[ListItem(Label(region), id=region) for region in get_all_regions()],
            id="regions",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.RegionSelected(selected.item.id))
        self.app.pop_screen()


class ProfileSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class ProfileSelected(Message):
        """"""

        def __init__(self, profile: str) -> None:
            self.profile = profile
            super().__init__()

    def compose(self) -> ComposeResult:
        profiles = self.parent.profiles
        yield ListView(
            *[ListItem(Label(profile), id=profile) for profile in profiles],
            id="profiles",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.ProfileSelected(selected.item.id))
        self.app.pop_screen()


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
        self.dyn_client = get_ddb_client(self.aws_profile, selected_region.region)

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
        table.clear()
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
