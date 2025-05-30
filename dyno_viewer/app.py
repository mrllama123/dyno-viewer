from textual import log, on, work
from textual.app import App, ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer
from textual.screen import Screen
from textual.worker import get_current_worker

from dyno_viewer.app_types import TableInfo
from dyno_viewer.aws.ddb import (
    get_ddb_client,
    query_items,
    scan_items,
    table_client_exist,
)
from dyno_viewer.aws.session import get_available_profiles
from dyno_viewer.components.screens import (
    HelpMenu,
    ProfileSelectScreen,
    QueryScreen,
    RegionSelectScreen,
    TableSelectScreen,
)
from dyno_viewer.components.screens.table_view_mode import TableViewer
from dyno_viewer.components.table import DataTableManager


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
        ("x", "exit", "Exit"),
        ("?", "switch_mode('help')", "help"),
    ]


    MODES = {
        "table": TableViewer,
        "help": HelpMenu,
    }

    def on_mount(self) -> None:
        self.switch_mode("table")

    # action methods
    async def action_exit(self) -> None:
        self.app.exit()


def run() -> None:
    app = DynCli()
    app.run()
