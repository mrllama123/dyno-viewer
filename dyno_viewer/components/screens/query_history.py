from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label

from dyno_viewer.aws.ddb import pretty_condition
from dyno_viewer.db.utils import get_query_history, list_query_history


class QueryHistoryScreen(ModalScreen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("n", "next_page", "Next Page"),
    ]

    next_page = reactive(1)
    total_pages = reactive(-1)

    class QueryHistoryResult(Message):
        def __init__(self, data) -> None:
            self.data = data
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("Query History:")
        yield DataTable(id="query_history_table")

    async def on_mount(self):
        table = self.query_exactly_one(DataTable)
        table.add_column("Time", key="time")
        table.add_column("Scan", key="scan")
        table.add_column("Key Condition", key="key_condition")
        table.add_column("Filter Conditions", key="filter_conditions")
        table.cursor_type = "row"
        table.focus()
        self.get_query_history()

    @work(exclusive=True)
    async def get_query_history(self):

        result = await list_query_history(
            self.app.db_session, page=self.next_page, page_size=20
        )
        self.total_pages = result.total_pages
        if result.total_pages > 1 and self.next_page < result.total_pages:
            self.next_page += 1

        table = self.query_one(DataTable)
        for item in result.items:
            query_params = item.to_query_params()
            boto_params = query_params.boto_params
            key_condition = (
                pretty_condition(boto_params["KeyConditionExpression"], is_key=True)
                if boto_params.get("KeyConditionExpression")
                else ""
            )
            filter_conditions = (
                pretty_condition(boto_params["FilterExpression"])
                if boto_params.get("FilterExpression")
                else ""
            )
            table.add_row(
                item.created_at.isoformat(sep=" ", timespec="seconds"),
                item.scan_mode,
                key_condition,
                filter_conditions,
                key=item.id,
            )

    @on(DataTable.RowSelected)
    async def on_row_selected(self, message: DataTable.RowSelected) -> None:
        query_history = await get_query_history(
            self.app.db_session, message.row_key.value
        )
        self.dismiss(query_history.to_query_params() if query_history else None)

    async def action_next_page(self) -> None:
        if self.next_page <= self.total_pages:
            self.get_query_history()
