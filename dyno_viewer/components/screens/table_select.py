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
from textual.widgets import Input
from dyno_viewer.aws.ddb import get_ddb_client, list_all_tables
from textual import log
from textual.reactive import reactive
from textual import work
from textual.worker import get_current_worker


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    dyn_client = reactive(None)

    next_token = reactive(None)

    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        self.tables = []
        super().__init__(name, id, classes)

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(Input(placeholder="Search for table"), ListView())
    
    def on_mount(self) -> None:
        table_input = self.query_one(Input)
        table_input.focus()

    @work(exclusive=True)
    def update_tables(self):
        worker = get_current_worker()
        if not worker.is_cancelled:
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

            new_tables = [
                table_name
                for table_name in dynamodb_tables
                if table_name not in self.tables
            ]

            def update_next_token(self, next_token):
                self.next_token = next_token

            self.app.call_from_thread(update_next_token, self, next_token)
            self.app.call_from_thread(self.tables.extend, new_tables)

    # on methods

    async def on_input_changed(self, changed: Input.Changed) -> None:
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
        input.focus()

    # watch methods

    async def watch_dyn_client(self, new_dyn_client) -> None:
        if new_dyn_client:
            self.update_tables()
            list_view = self.query_one(ListView)
            list_view.clear()
