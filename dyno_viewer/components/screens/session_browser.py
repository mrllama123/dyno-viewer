from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Markdown

from dyno_viewer.components.screens.create_rename_session import RenameCreateSession
from dyno_viewer.components.screens.select_session_group import SelectSessionGroup
from dyno_viewer.models import (
    Session,
)


class SessionBrowser(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Pop screen"),
        Binding("s", "select_session_group", "Select session group"),
        Binding("r", "rename_session", "Rename Session"),
        Binding("d", "delete_session", "Delete Session"),
        Binding("a", "add_session", "Add Session"),
    ]
    HELP = """
    ## Session Browser
    """

    DEFAULT_CSS = """

    DataTable {
        min-height: 50%;
    }
    Input {
        margin: 1 0;
    }
    """

    next_page = reactive(1)
    at_last_page = reactive(False)

    async def update_sessions_db(self, search: str = "", clear: bool = False) -> None:
        table = self.query_one(DataTable)
        if clear:
            table.clear()
            self.next_page = 1
            self.at_last_page = False

        if self.at_last_page:
            return
        result = await self.app.db_manager.list_sessions(
            page=self.next_page,
            search_name=search,
            session_group_id=self.app.session_group.session_group_id,
        )
        if len(result) == 0:
            self.at_last_page = True
            return
        self.next_page += 1
        for row in result:
            table.add_row(
                row.data.name,
                row.data.aws_profile,
                row.data.aws_region,
                row.data.table_name,
                key=row.key,
            )

    def update_sessions(self, search: str = ""):
        sessions = sorted(
            [
                screen_name
                for screen_name in self.app._installed_screens
                if self.app._installed_screens[screen_name].id.startswith("table_")
                and search in screen_name
            ]
            if search
            else [
                screen_name
                for screen_name in self.app._installed_screens
                if self.app._installed_screens[screen_name].id.startswith("table_")
            ]
        )
        if sessions:
            table = self.query_one(DataTable)
            table.clear()
            for screen_name in sessions:
                screen = self.app._installed_screens[screen_name]
                table.add_row(
                    screen_name,
                    screen.aws_profile,
                    screen.aws_region,
                    screen.table_name,
                    key=screen.id,
                )

    def compose(self) -> ComposeResult:
        yield Markdown("# Session Browser")
        yield Input(placeholder="Search session name")
        yield DataTable()

    async def on_mount(self):
        table = self.query_exactly_one(DataTable)
        table.add_column("Name", key="name")
        table.add_column("Aws profile", key="aws-profile")
        table.add_column("Aws region", key="aws-region")
        table.add_column("Table name", key="table-name")
        table.focus()
        table.cursor_type = "row"
        if self.app.session_group:
            self.worker_update_sessions_db()
        else:
            self.update_sessions()

    @on(DataTable.RowSelected)
    async def on_table_row_selected(self, event: DataTable.RowSelected):
        name = event.data_table.get_cell_at(Coordinate(event.cursor_row, 0))
        self.dismiss(name)

    @work(exclusive=True)
    async def worker_update_sessions_db(self) -> None:
        search_input = self.query_exactly_one(Input)
        await self.update_sessions_db(search_input.value)

    @work
    async def action_select_session_group(self):
        selected_session_group = await self.app.push_screen_wait(SelectSessionGroup())
        if not selected_session_group:
            return
        self.app.session_group = selected_session_group.session_group
        if selected_session_group.session_group:
            search_input = self.query_exactly_one(Input)
            # ensure that pagination is reset before updating session result
            await self.update_sessions_db(search_input.value, clear=True)
        else:
            self.app.install_table_viewer_screen()
            self.update_sessions()

    @work
    async def action_rename_session(self) -> None:
        table = self.query_exactly_one(DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            return
        renamed_session = await self.app.push_screen_wait(
            RenameCreateSession("Rename Session")
        )
        if not renamed_session:
            return

        # table.get_cell_at
        old_name = table.get_cell_at(table.cursor_coordinate)
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        self.log.info(f"old name {old_name}")

        self.app._installed_screens[renamed_session] = self.app._installed_screens.pop(
            old_name
        )

        if await self.app.db_manager.get_session(row_key.value):
            await self.app.db_manager.update_session(
                row_key.value, name=renamed_session
            )
        table.update_cell_at(table.cursor_coordinate, renamed_session)

    async def action_delete_session(self) -> None:
        table = self.query_exactly_one(DataTable)
        if table.row_count <= 1:
            self.notify(
                "Cannot delete due to only one session present.",
                severity="warning",
            )
            return
        if not table.is_valid_coordinate(table.cursor_coordinate):
            return

        name = table.get_cell_at(table.cursor_coordinate)
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        await self.app.remove_table_viewer_screen(name)
        if await self.app.db_manager.get_session(row_key.value):
            await self.app.db_manager.remove(row_key.value)
        table.remove_row(row_key)

    @work
    async def action_add_session(self) -> None:
        search_input = self.query_exactly_one(Input)
        name = await self.app.push_screen_wait(RenameCreateSession())
        if not name:
            return
        table_viewer = self.app.install_table_viewer_screen(name)
        if self.app.session_group:
            session = Session.from_table_viewer_screen(
                table_viewer, self.app.session_group.session_group_id, name
            )
            await self.app.db_manager.add_session(session)
            await self.update_sessions_db(search_input.value, clear=True)
        else:
            self.update_sessions(search_input.value)
