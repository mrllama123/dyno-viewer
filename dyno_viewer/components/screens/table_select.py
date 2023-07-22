from textual import log, on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input, OptionList
from textual.worker import get_current_worker

from dyno_viewer.aws.ddb import list_all_tables


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

        def __init__(self, table_result, next_token=None) -> None:
            self.table_result = table_result
            self.next_token = next_token
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for table", id="tableSelectInput")
        yield OptionList(id="optionDdbTableList")

    # worker methods

    @work(exclusive=True)
    def worker_list_tables(self, next_token=None):
        worker = get_current_worker()
        if not worker.is_cancelled:
            if next_token:
                list_tables_result, next_token = list_all_tables(
                    self.dyn_client,
                    Limit=10,
                    ExclusiveStartTableName=next_token,
                    paginate=False,
                )
            else:
                list_tables_result, next_token = list_all_tables(
                    self.dyn_client, Limit=10, paginate=False
                )

            self.post_message(self.TableListResult(list_tables_result, next_token))

    # on methods

    def on_mount(self) -> None:
        table_input = self.query_one(Input)
        table_input.focus()

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.value in self.tables:
            self.post_message(self.TableName(submitted.value))
            self.app.pop_screen()

    @on(TableListResult)
    async def on_table_list_result(self, result: TableListResult):
        new_tables = [
            table_name
            for table_name in result.table_result
            if table_name not in self.tables
        ]
        self.tables.extend(new_tables)
        self.next_token = result.next_token
        option_list = self.query_one(OptionList)
        option_list.add_options(self.tables)

    @on(Input.Changed, "#tableSelectInput")
    async def on_table_search_changed(self, changed: Input.Changed) -> None:
        table_list = self.query_one(OptionList)
        if changed.input.value:
            matched_tables = [
                table for table in self.tables if changed.input.value in table
            ]
            table_list.clear_options()
            if matched_tables:
                table_list.add_options(matched_tables)


    # watch methods

    async def watch_dyn_client(self, new_dyn_client) -> None:
        if new_dyn_client:
            option_list = self.query_one(OptionList)
            option_list.clear_options()
            self.worker_list_tables()
