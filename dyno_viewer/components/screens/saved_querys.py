from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Markdown

from dyno_viewer.aws.ddb import pretty_condition
from dyno_viewer.db.utils import (
    get_saved_query,
    list_saved_queries,
)


class SavedQueriesScreen(ModalScreen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("n", "next_page", "Next Page"),
    ]

    DEFAULT_CSS = """
    DataTable {
        min-height: 50%;
    }
    """

    next_page = reactive(1)
    total_pages = reactive(-1)

    class QueryHistoryResult(Message):
        def __init__(self, data) -> None:
            self.data = data
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Markdown("# Saved Queries:", id="title")
        yield DataTable(id="saved_queries_table")

    async def on_mount(self):
        table = self.query_exactly_one(DataTable)
        table.add_column("Name", key="name")
        table.add_column("Description", key="description")
        table.add_column("Created At", key="created_at")
        table.add_column("Scan", key="scan")
        table.add_column("Key Condition", key="key_condition")
        table.add_column("Filter Conditions", key="filter_conditions")
        table.cursor_type = "row"
        table.focus()
        self.get_saved_query()

    @work(exclusive=True)
    async def get_saved_query(self):

        result = await list_saved_queries(
            self.app.db_session, page=self.next_page, page_size=20
        )
        self.total_pages = result.total_pages
        if result.total_pages > 1 and self.next_page < result.total_pages:
            self.next_page += 1

        table = self.query_one(DataTable)
        for item in result.items:
            # this might eventually be slow with large data but for now it's ok
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
                item.name,
                item.description or "",
                item.created_at.isoformat(sep=" ", timespec="seconds"),
                item.scan_mode,
                key_condition,
                filter_conditions,
                key=item.id,
            )

    @on(DataTable.RowSelected)
    async def on_row_selected(self, message: DataTable.RowSelected) -> None:
        saved_query = await get_saved_query(self.app.db_session, message.row_key.value)
        self.dismiss(saved_query.to_query_params() if saved_query else None)

    async def action_next_page(self) -> None:
        if self.next_page <= self.total_pages:
            self.get_saved_query()
