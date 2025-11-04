from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Markdown

from dyno_viewer.aws.ddb import pretty_condition
from dyno_viewer.components.screens.confirm_dialogue import ConfirmDialogue
from dyno_viewer.db.utils import (
    delete_all_query_history,
    delete_query_history,
    get_query_history,
    list_query_history,
)


class QueryHistoryScreen(ModalScreen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        ("d", "delete_query", "Delete Query"),
        ("c", "delete_all_query_history", "Delete All Query History"),
        ("n", "next_page", "Next Page"),
    ]

    HELP = """
    ## Query History
    """

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
        yield Markdown("# Query History:", id="title")
        yield DataTable(id="query_history_table")

    async def on_mount(self):
        table = self.query_exactly_one(DataTable)
        table.add_column("Time", key="time")
        table.add_column("Scan", key="scan")
        table.add_column("Key Condition", key="key_condition")
        table.add_column("Filter Conditions", key="filter_conditions")
        table.cursor_type = "row"
        table.focus()
        self.retrieve_query_history()

    @work(exclusive=True)
    async def retrieve_query_history(self):

        result = await list_query_history(
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
                item.created_at.isoformat(sep=" ", timespec="seconds"),
                item.scan_mode,
                key_condition,
                filter_conditions,
                key=item.id,
            )

    @work(exclusive=True)
    async def remove_query_history_row(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            await delete_query_history(self.app.db_session, row_key.value)
            table.remove_row(row_key)

    @work(exclusive=True)
    async def remove_all_query_history_rows(self) -> None:
        await delete_all_query_history(self.app.db_session)
        table = self.query_one(DataTable)
        table.clear()

    @on(DataTable.RowSelected)
    async def on_row_selected(self, message: DataTable.RowSelected) -> None:
        query_history = await get_query_history(
            self.app.db_session, message.row_key.value
        )
        self.dismiss(query_history.to_query_params() if query_history else None)

    async def action_next_page(self) -> None:
        if self.next_page <= self.total_pages:
            self.retrieve_query_history()

    async def action_delete_query(self) -> None:
        self.remove_query_history_row()

    @work
    async def action_delete_all_query_history(self) -> None:
        confirm = await self.app.push_screen_wait(
            ConfirmDialogue("Are you sure you want to delete all query history?")
        )
        if confirm:
            self.remove_all_query_history_rows()
