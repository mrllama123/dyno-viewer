from textual.app import App
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive

from dyno_viewer.components.screens.help import HelpScreen
from dyno_viewer.components.screens.table_view import TableViewer
from dyno_viewer.db.utils import (
    start_async_session,
)
from dyno_viewer.models import TableInfo


class QueryResult(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


class UpdateDynTableInfo(Message):
    def __init__(self, table_info: TableInfo) -> None:
        self.table_info = table_info
        super().__init__()


class DynCli(App):

    BINDINGS = [
        Binding("x", "exit", "Exit", tooltip="Exit the application"),
        Binding("?", "show_help", "Help", tooltip="Show help", priority=True),
    ]

    db_session = reactive(None)

    async def on_mount(self) -> None:
        # Initialize the async DB session (SQLAlchemy)
        self.db_session = await start_async_session()
        self.install_screen(TableViewer(), name="table")
        self.push_screen("table")

    # action methods
    async def action_exit(self) -> None:
        self.app.exit()

    def action_show_help(self):
        self.push_screen(HelpScreen())


def run() -> None:
    app = DynCli()
    app.run()
