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
from textual import work, on
from textual.suggester import SuggestFromList, SuggestionReady
from textual.worker import get_current_worker


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    dyn_client = reactive(None, always_update=True)

    next_token = reactive(None)

    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        self.tables = []
        super().__init__(name, id, classes)

    # message classes

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    class TableListResult(Message):
        """return result from listing tables"""

        def __init__(self, table_result, next_token) -> None:
            self.table_result = table_result
            self.next_token = next_token
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for table", id="tableSelectInput")

    # worker methods

    @work(exclusive=True)
    def update_tables(self, next_token):
        worker = get_current_worker()
        if not worker.is_cancelled:
            if next_token:
                dynamodb_tables, next_token = list_all_tables(
                    self.dyn_client,
                    Limit=10,
                    ExclusiveStartTableName=next_token,
                    paginate=False,
                )
            else:
                dynamodb_tables, next_token = list_all_tables(
                    self.dyn_client, Limit=10, paginate=False
                )

            self.post_message(self.TableListResult(dynamodb_tables, next_token))

    # on methods

    def on_mount(self) -> None:
        table_input = self.query_one(Input)
        table_input.focus()



    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.value in self.tables:
            self.post_message(self.TableName(submitted.value))
            self.app.pop_screen()

    async def on_list_view_selected(self, selected: ListView.Selected) -> None:
        input = self.query_one(Input)
        input.value = selected.item.id
        input.focus()

    @on(SuggestionReady)
    async def on_table_suggest(self, suggestion_ready: SuggestionReady) -> None:

        if not suggestion_ready.suggestion and self.next_token:
            self.update_tables(self.next_token)
            

    @on(TableListResult)
    async def on_table_list_result(self, result: TableListResult):
        new_tables = [
            table_name
            for table_name in result.table_result
            if table_name not in self.tables
        ]
        self.tables.extend(new_tables)
        self.next_token = result.next_token
        self.query_one(Input).suggester = SuggestFromList(
            self.tables, case_sensitive=False
        )

    # watch methods

    async def watch_dyn_client(self, new_dyn_client) -> None:
        if new_dyn_client:

            self.update_tables(self.next_token)
