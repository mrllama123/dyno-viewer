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
from dyn_cli.aws.sts import get_available_profiles
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
    
    def change_table_data(self, table_name):
        dyn_table_client = get_table_client(table_name)
        table = self.query_one(DataTable)
        results, next_token = scan_items(dyn_table_client, paginate=False, Limit=10)
        self.data_table = pd.DataFrame(results)
        
        table.clear()
        table.add_columns(*self.data_table.columns.tolist())
        table.add_rows(self.data_table.values.tolist())


    


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:
        dyn_client = get_ddb_client()
        dynamodb_tables = dyn_client.list_tables()["TableNames"]

        yield ListView(
            *[ListItem(Label(table), id=table) for table in dynamodb_tables],
            id="dynTablesSelect",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.TableName(selected.item.id))
        self.app.pop_screen()


class DynCli(App):
    BINDINGS = [
        ("x", "exit", "Exit"),
        # ("p", "profile", "Profile")
        ("t", "push_screen('tableSelect')", "Table"),
    ]
    SCREENS = {"tableSelect": TableSelectScreen()}

    profiles = reactive(get_available_profiles())

    aws_profile = reactive("default")

    table_name = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield Footer()
        yield Horizontal(Label(self.table_name) ,DynTable())

    async def on_table_select_screen_table_name(
        self, table_name: TableSelectScreen.TableName
    ) -> None:
        self.table_name = table_name.table

        # profile_list = ListView(*[ListItem(Label(profile)) for profile in self.profiles])
        # self.mount(profile_list)

    async def action_exit(self) -> None:
        self.app.exit()

    def watch_table_name(self, new_table_name: str) -> None: 
        if new_table_name != "":
            table = self.query_one(DynTable)
            table.change_table_data(new_table_name)



def main() -> None:
    app = DynCli()
    app.run()


if __name__ == "__main__":
    main()
