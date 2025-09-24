import pytest
from textual.app import App, on
from textual.widgets import DataTable, Footer
from textual.reactive import reactive


from dyno_viewer.aws.ddb import get_ddb_client
from dyno_viewer.components.screens.query import QueryScreen
from dyno_viewer.components.screens.table_view_mode import TableViewer


class TableViewModeApp(App):
    aws_profile = reactive(None)
    aws_region = reactive("ap-southeast-2")
    SCREENS = {
        "query": QueryScreen,
    }
    MODES = {
        "table": TableViewer,
    }

    def on_mount(self) -> None:
        self.switch_mode("table")

    @on(QueryScreen.QueryParametersChanged)
    def query_screen_parameters_changed(
        self, query_params: QueryScreen.QueryParametersChanged
    ) -> None:
        if isinstance(self.screen, TableViewer):
            self.screen.query_params = query_params.params

    # HACK: this is a work around as the query screen can't send the event to the TableViewer screen
    # and we want to persist this screen across an session
    @on(QueryScreen.RunQuery)
    async def query_screen_run_query(self, run_query: QueryScreen.RunQuery) -> None:
        table_viewer = self.screen
        if isinstance(table_viewer, TableViewer):
            await table_viewer.run_query(run_query)


async def test_table_view_mode_initialization():
    async with TableViewModeApp().run_test() as pilot:
        assert isinstance(pilot.app.screen, TableViewer)
        table_viewer: TableViewer = pilot.app.screen
        assert table_viewer.table_name == ""
        assert table_viewer.data == []
        assert table_viewer.query_params is None
        assert table_viewer.table_info is None
        assert table_viewer.dyn_query_params == {}
        assert table_viewer.query_screen_parameters is None
        assert table_viewer.table_client is None

        data_table = table_viewer.query_one(DataTable)
        assert data_table is not None
        assert len(data_table.columns) == 0
        assert len(data_table.rows) == 0


async def test_table_view_mode_set_table_name(ddb_tables):
    async with TableViewModeApp().run_test() as pilot:
        table_viewer: TableViewer = pilot.app.screen
        assert isinstance(table_viewer, TableViewer)
        table_name = ddb_tables[0].name

        # set dyn_client
        pilot.app.dyn_client = get_ddb_client(
            region_name=pilot.app.aws_region, profile_name=pilot.app.aws_profile
        )

        # set table name
        table_viewer.table_name = table_name
        table_viewer.update_table_client()
        await pilot.pause()

        assert table_viewer.table_name == table_name
        assert table_viewer.table_client is not None

        # # check table info is set
        assert table_viewer.table_info is not None
        assert table_viewer.table_info["tableName"] == table_name

        data_table = table_viewer.query(DataTable)
        assert data_table
        # check data table is loading
        assert data_table[0].loading is False  # loading should be false after data is loaded
        assert len(data_table[0].columns) > 0  # columns should be set after data is loaded
