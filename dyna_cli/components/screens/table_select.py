from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Label,
)
from textual.screen import Screen
from textual.events import Key
from textual.message import Message
from textual.containers import Vertical
from textual.widgets import  Input
from dyna_cli.aws.ddb import get_ddb_client, list_all_tables
from textual import log
from textual.reactive import reactive


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    tables = []

    dyn_client = reactive(get_ddb_client())

    next_token = reactive(None)

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(Input(placeholder="Search for table"), ListView())

    def update_tables(self):
        if self.next_token:
            dynamodb_tables, next_token = list_all_tables(
                self.dyn_client,
                Limit=10,
                ExclusiveStartTableName=self.next_token,
                paginate=False,
            )
        else:
            dynamodb_tables, next_token = list_all_tables(
                self.dyn_client, Limit=10, paginate=False
            )

        self.next_token = next_token
        self.tables.extend(dynamodb_tables)

    # on methods

    def on_input_changed(self, changed: Input.Changed) -> None:
        # TODO make the matching more smarter
        match_tables = [table for table in self.tables if changed.value in table]

        if len(match_tables) == 0:
            self.update_tables()

        list_view = self.query_one(ListView)
        list_view.clear()
        for matched_table in match_tables:
            list_view.append(ListItem(Label(matched_table), id=matched_table))

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.value in self.tables:
            self.post_message(self.TableName(submitted.value))
            self.app.pop_screen()

    async def on_list_view_selected(self, selected: ListView.Selected) -> None:
        input = self.query_one(Input)
        input.value = selected.item.id

    # watch methods

    async def watch_dyn_client(self, new_dyn_client) -> None:
        self.update_tables()
        list_view = self.query_one(ListView)
        list_view.clear()



