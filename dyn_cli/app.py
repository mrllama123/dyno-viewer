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

    def change_table_data(self, table_name, region):
        dyn_table_client = get_table_client(table_name, region)
        table = self.query_one(DataTable)
        results, next_token = scan_items(dyn_table_client, paginate=False, Limit=10)
        self.data_table = pd.DataFrame(results)

        table.clear()
        table.add_columns(*self.data_table.columns.tolist())
        table.add_rows(self.data_table.values.tolist())

    def clear_table(self):
        table = self.query_one(DataTable)
        table.clear()


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


class DynCli(App):
    BINDINGS = [
        ("x", "exit", "Exit"),
        # ("p", "profile", "Profile")
        ("t", "push_screen('tableSelect')", "Table"),
        ("r", "push_screen('regionSelect')", "Region"),
    ]
    SCREENS = {"tableSelect": TableSelectScreen(), "regionSelect": RegionSelectScreen()}

    profiles = reactive(get_available_profiles())

    aws_profile = reactive("default")

    table_name = reactive("", layout=True)

    aws_region = reactive("ap-southeast-2")

    def compose(self) -> ComposeResult:
        yield Footer()
        yield Horizontal(Label(self.table_name), DynTable())



    # on methods

    async def on_region_select_screen_region_selected(
        self, selected_region: RegionSelectScreen.RegionSelected
    ) -> None:
        self.aws_region = selected_region.region

    async def on_table_select_screen_table_name(
        self, table_name: TableSelectScreen.TableName
    ) -> None:
        self.table_name = table_name.table

    # action methods

    async def action_exit(self) -> None:
        self.app.exit()

    # watcher methods

    def watch_table_name(self, new_table_name: str) -> None:
        """update DynTable with new table data"""
        if new_table_name != "":
            table = self.query_one(DynTable)
            table.change_table_data(new_table_name, self.aws_region)

    def watch_aws_region(self, old_region_name: str, new_region_name: str) -> None:
        if old_region_name != new_region_name:
            table = self.query_one(DynTable)
            
            # TODO  move to func
            dyn_client = get_ddb_client(region_name=self.aws_region)
            dynamodb_tables = dyn_client.list_tables()["TableNames"]

            if self.table_name not in dynamodb_tables:
                table.clear_table()
            else:
                table.change_table_data(self.table_name, new_region_name)


def main() -> None:
    app = DynCli()
    app.run()


if __name__ == "__main__":
    main()
