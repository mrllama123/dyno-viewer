import uuid

from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive

from dyno_viewer.components.screens.app_options import AppOptions
from dyno_viewer.components.screens.create_rename_session import (
    RenameCreateSession,
)
from dyno_viewer.components.screens.help import Help
from dyno_viewer.components.screens.table_session_browser import (
    TableSessionBrowser,
)
from dyno_viewer.components.screens.table_view import TableViewer
from dyno_viewer.constants import CONFIG_DIR_NAME, DATABASE_FILE_PATH
from dyno_viewer.db.data_store import setup_connection
from dyno_viewer.db.queries import delete_all_saved_queries
from dyno_viewer.messages import ClearQueryHistory
from dyno_viewer.models import Config
from dyno_viewer.util.path import ensure_config_dir


class DynCli(App):

    BINDINGS = [
        Binding("x", "exit", "Exit", tooltip="Exit the application"),
        Binding(
            "n",
            "create_new_table_viewer_session",
            "New Table Viewer Session",
            tooltip="Create a new table viewer session",
            show=False,
        ),
        Binding("s", "select_session", "Select session", show=False),
        Binding("`", "show_options", "Options", show=False),
        Binding("?", "show_help", "Help", tooltip="Show help", priority=True),
    ]

    db_session = reactive(None)
    app_config = reactive(Config.load_config())

    async def on_mount(self) -> None:
        # Initialize the async DB session (SQLAlchemy)
        ensure_config_dir(CONFIG_DIR_NAME)
        self.db_session = await setup_connection(DATABASE_FILE_PATH)
        # self.db_session = await start_async_session()
        self.install_screen(
            TableViewer(id=f"table_{uuid.uuid4()}"), name="default_table"
        )
        self.push_screen("default_table")

    async def on_unmount(self) -> None:
        if self.db_session:
            await self.db_session.close()

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
    async def action_create_new_table_viewer_session(self) -> None:
        if not isinstance(self.screen, TableViewer):
            return
        session = await self.app.push_screen_wait(
            RenameCreateSession("Update Table Viewer Session")
        )
        if session:
            self.install_screen(TableViewer(id=f"table_{uuid.uuid4()}"), name=session)
            self.app.push_screen(session)

    @work
    async def action_select_session(self) -> None:
        """Open the session select screen."""
        session = await self.app.push_screen_wait(TableSessionBrowser())
        if session:
            self.app.push_screen(session)

    @work(exclusive=True, group="purge_query_history")
    async def worker_delete_query_history(self) -> None:
        """Clear all query history from the database."""
        if not self.db_session:
            return
        await delete_all_saved_queries(self.db_session)
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
