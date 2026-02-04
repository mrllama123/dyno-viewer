import uuid

from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive

from dyno_viewer.components.screens.app_options import AppOptions
from dyno_viewer.components.screens.create_session_group import CreateSessionGroup
from dyno_viewer.components.screens.help import Help
from dyno_viewer.components.screens.select_session_group import SelectSessionGroup
from dyno_viewer.components.screens.session_browser import SessionBrowser
from dyno_viewer.components.screens.table_view import TableViewer
from dyno_viewer.constants import CONFIG_DIR_NAME, DATABASE_FILE_PATH
from dyno_viewer.db.manager import DatabaseManager
from dyno_viewer.messages import ClearQueryHistory
from dyno_viewer.models import Config, Session, SessionGroup
from dyno_viewer.util.path import ensure_config_dir


class DynCli(App):
    BINDINGS = [
        Binding("x", "exit", "Exit", tooltip="Exit the application"),
        Binding(
            "g",
            "create_session_group",
            "Create session group",
            tooltip="Create a group to hold sessions",
        ),
        Binding("v", "select_session_group", "Select session group"),
        Binding("j", "session_browser", "Session Browser"),
        Binding("`", "show_options", "Options", show=False),
        Binding("?", "show_help", "Help", tooltip="Show help", priority=True),
    ]

    db_manager: DatabaseManager | None = reactive(None)
    app_config = reactive(Config.load_config())
    session_group = reactive(None)

    def _remove_all_table_viewer_screens(self):
        self.pop_screen()
        updated_installed_screens = {
            name: installed_screen
            for name, installed_screen in self._installed_screens.items()
            if not installed_screen.id.startswith("table_")
        }
        self._installed_screens = updated_installed_screens

    def install_table_view_from_session(self, session: Session):
        table_viewer = TableViewer(id=session.session_id)
        if session.aws_profile:
            table_viewer.aws_profile = session.aws_profile
        if session.aws_region:
            table_viewer.aws_region = session.aws_region
        if session.table_name:
            table_viewer.table_name = session.table_name

        self.install_screen(table_viewer, name=session.name)
        return table_viewer

    async def copy_existing_screens_to_sessions(self, session_group: SessionGroup):
        workspace_sessions = [
            Session.from_table_viewer_screen(
                screen, session_group.session_group_id, screen_name
            )
            for screen_name, screen in self._installed_screens.items()
            if screen.id.startswith("table_")
        ]
        await self.db_manager.add_sessions(workspace_sessions)
        self.notify(f"New workspace {session_group.name} created")

    async def remove_table_viewer_screen(self, screen_name: str):
        if screen_name not in self._installed_screens:
            return
        del self._installed_screens[screen_name]

    def install_table_viewer_screen(
        self, screen_name: str = "default_table", session: Session | None = None
    ) -> TableViewer:
        """
        Install a new TableViewer screen and optionally associate it with a session. If no session is provided will just create screen

        :param screen_name: Name of the new TableViewer screen, Will use session name if set
        :type screen_name: str
        :param session: session object, if not provided will create screen without session
        :type session: Session | None
        :return: TableViewer screen
        :rtype: TableViewer
        """
        if session:
            return self.install_table_view_from_session(session)
        table_viewer = TableViewer(id=f"table_{uuid.uuid4()}")
        self.install_screen(table_viewer, screen_name)
        return table_viewer

    async def on_mount(self) -> None:
        # Initialize the database connection
        ensure_config_dir(CONFIG_DIR_NAME)
        self.db_manager = DatabaseManager(DATABASE_FILE_PATH)
        await self.db_manager.setup()
        if self.app_config.startup_session_group:
            self.session_group = await self.db_manager.get_session_group_by_name(
                self.app_config.startup_session_group
            )
            list_sessions = await self.db_manager.list_sessions()
            if len(list_sessions) == 0:

                return
            for row in list_sessions:
                self.install_table_viewer_screen(session=row.data)
            self.push_screen(list_sessions[0].data.name)
        else:
            self.install_screen(
                TableViewer(id=f"table_{uuid.uuid4()}"), name="default_table"
            )
            self.push_screen("default_table")

    async def on_unmount(self) -> None:
        if self.db_manager:
            await self.db_manager.close()

    @on(ClearQueryHistory)
    async def process_clear_query_history_request(self, _: ClearQueryHistory) -> None:
        self.worker_delete_query_history()

    # action methods
    async def action_exit(self) -> None:
        self.app.exit()

    def action_show_help(self):
        self.push_screen(Help())

    def action_show_options(self) -> None:
        self.push_screen(AppOptions())

    @work
    async def action_create_session_group(self):
        name, copy_current_sessions = await self.push_screen_wait(CreateSessionGroup())
        if not name:
            return

        # Create the workspace in the database
        session_group = SessionGroup(name=name)
        await self.db_manager.add_session_group(session_group)
        self.session_group = session_group
        # Create the workspace session in the database
        if copy_current_sessions:
            await self.copy_existing_screens_to_sessions(session_group)
            return
        self._remove_all_table_viewer_screens()
        table_viewer = TableViewer(id=f"table_{uuid.uuid4()}")
        self.install_screen(table_viewer, name="default_table")
        workspace_session = Session.from_table_viewer_screen(
            table_viewer, session_group.session_group_id, "default_table"
        )
        await self.db_manager.add_session(workspace_session)
        self.push_screen("default_table")
        self.notify(f"New workspace {session_group.name} created")

    @work
    async def action_select_session_group(self):
        selected_session_group = await self.app.push_screen_wait(SelectSessionGroup())
        if not selected_session_group:
            return

        self.session_group = selected_session_group.session_group

        self._remove_all_table_viewer_screens()
        if not self.session_group:
            self.install_table_viewer_screen()
            return

        # list though 1 page and get first one (can get more in session browser). In future maybe we have setting for default session
        list_sessions = await self.db_manager.list_sessions()
        if len(list_sessions) == 0:
            return
        for row in list_sessions:
            self.install_table_viewer_screen(session=row.data)
        self.push_screen(list_sessions[0].data.name)

    @work
    async def action_session_browser(self):
        screen_name: str = await self.push_screen_wait(SessionBrowser())
        if not screen_name:
            return
        self.push_screen(screen_name)

    @work(exclusive=True, group="purge_query_history")
    async def worker_delete_query_history(self) -> None:
        """Clear all query history from the database."""
        if not self.db_manager:
            return
        await self.db_manager.remove_all_query_history()
        self.notify("Query history cleared.")

    def watch_theme(self, new_theme: str) -> None:
        """Called automatically when the theme changes."""
        if not self.app_config:
            return
        if new_theme == self.app_config.theme:
            return
        self.app_config.theme = new_theme
        self.app_config.save_config()

    def watch_app_config(self, new_value: Config) -> None:
        if new_value:
            if new_value.theme != self.theme:
                self.theme = new_value.theme


def run() -> None:
    app = DynCli()
    app.run()
