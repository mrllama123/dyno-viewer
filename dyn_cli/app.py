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
from dyn_cli.aws.ddb import scan_items, get_ddb_client


class DynTable(Widget):
    def compose(self) -> ComposeResult:
        yield DataTable()

    async def on_mount(self) -> None:
        dynamodb_client = boto3.resource("dynamodb").Table("dummy-bank")
        results, next_token = scan_items(dynamodb_client, paginate=False, Limit=10)
        df = pd.DataFrame(results)

        table = self.query_one(DataTable)

        table.add_columns(*df.columns.tolist())
        table.add_rows(df.values.tolist())



class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class Selected(Message):
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

    async def on_list_view_selected(self, item: ListItem) -> None:
        self.post_message(self.Selected(item.id))
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

    def compose(self) -> ComposeResult:
        yield Footer()
        yield Horizontal(DynTable())

    # async def action_profile(self) -> None:
    #     profile_list = ListView(*[ListItem(Label(profile)) for profile in self.profiles])
    #     self.mount(profile_list)

    async def action_exit(self) -> None:
        self.app.exit()


def main() -> None:
    app = DynCli()
    app.run()


if __name__ == "__main__":
    main()
