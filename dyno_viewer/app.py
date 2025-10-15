from textual import log, on, work
from textual.app import App
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive

from dyno_viewer.aws.ddb import (
    get_ddb_client,
)
from dyno_viewer.components.screens import (
    ProfileSelectScreen,
    RegionSelectScreen,
)
from dyno_viewer.components.screens.query import QueryScreen
from dyno_viewer.components.screens.table_view_mode import TableViewer
from dyno_viewer.db.utils import (
    add_query_history,
    start_async_session,
)
from dyno_viewer.models import QueryParameters, TableInfo


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
        Binding("z", "switch_mode('table')", "Table Viewer", show=False),
        Binding("p", "select_profile", "Profile", tooltip="Select AWS Profile"),
        Binding("r", "select_region", "Region", tooltip="Select AWS Region"),
        Binding("?", "show_help", "Help", tooltip="Show help"),
    ]
    SCREENS = {
        "query": QueryScreen,
    }

    aws_profile = reactive(None)
    aws_region = reactive("ap-southeast-2")
    dyn_client = reactive(
        get_ddb_client(region_name="ap-southeast-2", profile_name=None)
    )
    db_session = reactive(None)
    is_help_visible = reactive(False)

    MODES = {
        "table": TableViewer,
    }

    async def on_mount(self) -> None:
        # Initialize the async DB session (SQLAlchemy)
        self.db_session = await start_async_session()
        self.switch_mode("table")

    @on(QueryScreen.QueryParametersChanged)
    async def query_screen_parameters_changed(
        self, query_params: QueryScreen.QueryParametersChanged
    ) -> None:
        if isinstance(self.screen, TableViewer):
            self.screen.query_params = query_params.params
            self.append_query_to_history(query_params.params)

    # HACK: this is a work around as the query screen can't send the event to the TableViewer screen
    # and we want to persist this screen across an session
    @on(QueryScreen.RunQuery)
    async def query_screen_run_query(self, run_query: QueryScreen.RunQuery) -> None:
        table_viewer = self.screen
        if isinstance(table_viewer, TableViewer):
            await table_viewer.run_query(run_query)

    async def watch_aws_profile(self, new_profile: str | None) -> None:
        log.info(f"App: AWS Profile changed to: {new_profile}")
        self.dyn_client = get_ddb_client(
            region_name=self.aws_region, profile_name=new_profile
        )
        # Notify TableViewer if it's the active screen
        if isinstance(self.screen, TableViewer):
            self.screen.aws_profile = new_profile  # Pass the new profile
            self.screen.dyn_client = self.dyn_client  # Pass the new client
            self.screen.update_table_client()

    async def watch_aws_region(self, new_region: str) -> None:
        log.info(f"App: AWS Region changed to: {new_region}")
        self.dyn_client = get_ddb_client(
            region_name=new_region, profile_name=self.aws_profile
        )
        # Notify TableViewer if it's the active screen
        if isinstance(self.screen, TableViewer):
            self.screen.aws_region = new_region  # Pass the new region
            self.screen.dyn_client = self.dyn_client  # Pass the new client
            self.screen.update_table_client()

    # action methods
    async def action_exit(self) -> None:
        self.app.dyn_client.close()
        self.app.exit()

    def action_show_help(self):
        if self.is_help_visible:
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()
        self.is_help_visible = not self.is_help_visible

    @work
    async def action_select_profile(self) -> None:
        """Open the profile select screen."""
        profile = await self.push_screen_wait(ProfileSelectScreen())
        if profile:
            self.aws_profile = profile

    @work
    async def action_select_region(self) -> None:
        """Open the region select screen."""
        region = await self.push_screen_wait(RegionSelectScreen())
        if region:
            self.aws_region = region

    @work(exclusive=True)
    async def append_query_to_history(self, params: QueryParameters) -> None:
        """Add the query to the history."""
        if not params.filter_conditions and not params.key_condition:
            return
        await add_query_history(self.db_session, params)


def run() -> None:
    app = DynCli()
    app.run()
