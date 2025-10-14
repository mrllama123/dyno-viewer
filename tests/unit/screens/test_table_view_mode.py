import pytest
from textual.app import App, on
from textual.widgets import DataTable, Footer
from textual.reactive import reactive


from dyno_viewer.aws.ddb import get_ddb_client
from dyno_viewer.components.screens.query import QueryScreen
from dyno_viewer.components.screens.table_view_mode import TableViewer
from dyno_viewer.components.table import DataTableManager
from dyno_viewer.components.table import DataTableManager
from dyno_viewer.models import KeyCondition, QueryParameters


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




async def test_table_view_mode_initialization():
    async with TableViewModeApp().run_test() as pilot:
        assert isinstance(pilot.app.screen, TableViewer)
        table_viewer: TableViewer = pilot.app.screen
        assert table_viewer.table_name == ""
        assert table_viewer.data == []
        assert table_viewer.query_params is None
        assert table_viewer.table_info is None
        assert table_viewer.table_client is None

        data_table = table_viewer.query_one(DataTable)
        assert data_table is not None
        assert len(data_table.columns) == 0
        assert len(data_table.rows) == 0


async def test_table_view_mode_set_table_name(ddb_table):
    async with TableViewModeApp().run_test() as pilot:
        table_viewer: TableViewer = pilot.app.screen
        assert isinstance(table_viewer, TableViewer)
        table_name = ddb_table.name

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
        assert (
            data_table[0].loading is False
        )  # loading should be false after data is loaded
        assert (
            len(data_table[0].columns) > 0
        )  # columns should be set after data is loaded


async def test_table_view_mode_run_query(ddb_table_with_data, ddb_table):
    async with TableViewModeApp().run_test() as pilot:
        table_viewer: TableViewer = pilot.app.screen
        assert isinstance(table_viewer, TableViewer)
        table_name = ddb_table.name

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

        query_data_table = table_viewer.query(DataTable)
        assert query_data_table
        data_table = query_data_table[0]
        # check data table is loading
        assert (
            data_table.loading is False
        )  # loading should be false after data is loaded
        assert len(data_table.columns) > 0  # columns should be set after data is loaded

        # run a query to get customer with pk customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d
        pilot.app.post_message(
            QueryScreen.QueryParametersChanged(
                QueryParameters(
                    scan_mode=False,
                    table_name=table_name,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    key_condition=KeyCondition(
                        partitionKeyValue="customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
                    ),
                )
            )
        )
        await pilot.pause()

        # check data table is updated
        assert data_table.row_count == 1
        rows = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert rows == [
            [
                "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
                "CUSOMER",
                "CUSTOMER",
                "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
                None,
                None,
                "test1",
            ]
        ]

async def test_table_view_mode_pagination(ddb_table_with_data, ddb_table):
    async with TableViewModeApp().run_test() as pilot:
        table_viewer: TableViewer = pilot.app.screen
        assert isinstance(table_viewer, TableViewer)
        table_name = ddb_table.name

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

        query_data_table = table_viewer.query(DataTable)
        data_table_manager = table_viewer.query_one(DataTableManager)       
        assert query_data_table
        data_table = query_data_table[0]
        # check data table is loading
        assert (
            data_table.loading is False
        )  # loading should be false after data is loaded
        assert len(data_table.columns) > 0  # columns should be set after data is loaded

        page_zero = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert len(table_viewer.data) == 1
        assert len(page_zero) == 50

        # go to next page
        await pilot.press("]")
        await pilot.pause()
        assert data_table_manager.page_index == 1
        assert len(table_viewer.data) == 2  # should have 2 pages of data now
        page_one = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert len(page_one) == 50
        assert page_one != page_zero

        # go to previous page
        await pilot.press("[")
        await pilot.pause()
        page_back = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert page_back == page_zero

        # go to next page again
        await pilot.press("]")
        await pilot.pause()
        assert data_table_manager.page_index == 1
        page_one_again = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert page_one_again == page_one

        # go to next page 
        await pilot.press("]")
        await pilot.pause()
        assert data_table_manager.page_index == 2
        assert len(table_viewer.data) == 3  # should have 3 pages of data now
        page_two = [data_table.get_row_at(i) for i in range(0, data_table.row_count)]
        assert len(page_two) == 50  # last page should have 50 items
        assert page_two != page_one
        assert page_two != page_zero



