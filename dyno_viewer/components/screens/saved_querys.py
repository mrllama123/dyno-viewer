from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Markdown

from dyno_viewer.aws.ddb import pretty_condition
from dyno_viewer.components.screens.confirm_dialogue import ConfirmDialogue
from dyno_viewer.db.utils import (
    delete_all_saved_queries,
    delete_saved_query,
    get_saved_query,
    list_saved_queries,
)


class SavedQueriesScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Pop screen"),
        Binding("n", "next_page", "Next Page"),
        Binding("d", "delete_saved_query", "Delete Saved Query"),
        Binding("c", "delete_all_saved_queries", "Delete All Saved Queries"),
    ]

    HELP = """
    ## Saved Queries
    """

    DEFAULT_CSS = """
    #saved_queries_screen {
        background: $boost;
    }
    DataTable {
        min-height: 50%;
    }
    Input {
        margin: 1 0;
    }
    """

    next_page = reactive(1)
    total_pages = reactive(1)

    class QueryHistoryResult(Message):
        def __init__(self, data) -> None:
            self.data = data
            super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="saved_queries_screen"):
            yield Markdown("# Saved Queries:", id="title")
            yield Input(placeholder="Search Saved Queries", id="search_saved_queries")
            yield DataTable(id="saved_queries_table")

    async def on_mount(self):
        table = self.query_exactly_one(DataTable)
        search_input = self.query_one("#search_saved_queries", Input)
        search_input.focus()
        table.add_column("Name", key="name")
        table.add_column("Description", key="description")
        table.add_column("Created At", key="created_at")
        table.add_column("Scan", key="scan")
        table.add_column("Key Condition", key="key_condition")
        table.add_column("Filter Conditions", key="filter_conditions")
        table.cursor_type = "row"
        self.get_saved_query()

    @work(exclusive=True)
    async def get_saved_query(self, search: str = ""):

        result = await list_saved_queries(
            self.app.db_session, page=self.next_page, search=search
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

    @on(Input.Submitted, "#search_saved_queries")
    async def search_saved_queries(self, message: Input.Submitted) -> None:
        self.next_page = 1
        table = self.query_one(DataTable)
        table.clear()
        self.get_saved_query(search=message.value)

    @work
    async def action_delete_saved_query(self) -> None:
        confirm = await self.app.push_screen_wait(
            ConfirmDialogue("Are you sure you want to delete this saved query?")
        )
        if confirm:
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
                await delete_saved_query(self.app.db_session, row_key.value)
                table.remove_row(row_key)

    @work
    async def action_delete_all_saved_queries(self) -> None:
        confirm = await self.app.push_screen_wait(
            ConfirmDialogue("Are you sure you want to delete all saved queries?")
        )
        if confirm:
            table = self.query_one(DataTable)
            await delete_all_saved_queries(self.app.db_session)
            table.clear()

    def action_next_page(self) -> None:
        if self.next_page == 1 and self.total_pages == 1:
            return
        if self.next_page <= self.total_pages:
            self.get_saved_query(
                search=self.query_one("#search_saved_queries", Input).value
            )
