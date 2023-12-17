import pytest
from dyno_viewer.components.table import DataDynTable


@pytest.fixture(scope="function")
def dyn_cli(mocker, ddb_table_with_data, dynamodb):
    mocker.patch("dyno_viewer.app.get_ddb_client", return_value=dynamodb)

    from dyno_viewer.app import DynCli

    return DynCli

async def test_select_table(dyn_cli):
    # from dyno_viewer.app import DynCli

    async with dyn_cli().run_test() as pilot:
        assert pilot.app.dyn_client
        await pilot.press("t", "tab", "down", "enter", "enter")
        assert pilot.app.table_client

        data_table = pilot.app.query_one(DataDynTable)
        await pilot.pause()
        assert data_table.row_count == 50
        await pilot.press("x")

async def test_select_multi_table(dyn_cli):
    # from dyno_viewer.app import DynCli
    async with dyn_cli().run_test() as pilot:
        assert pilot.app.dyn_client
        await pilot.press("t", "tab", "down", "enter", "enter")
        assert pilot.app.table_client
        assert pilot.app.table_name == "dawnstar"

        data_table = pilot.app.query_one(DataDynTable)
        await pilot.pause()
        assert data_table.row_count == 50
        await pilot.press("t", "tab", "down", "enter", "enter")
        assert pilot.app.table_name == "falkreath"
        await pilot.press("x")


# async def test_table_pagination(ddb_table_with_data):
#     from dyno_viewer.app import DynCli
#     from dyno_viewer.components.table import DataDynTable

#     async with DynCli().run_test() as pilot:
#         assert pilot.app.dyn_client
#         await pilot.press("t", "tab", "down", "enter", "enter")
#         assert pilot.app.table_client

#         data_table = pilot.app.query_one(DataDynTable)
#         await pilot.pause()
#         assert data_table.row_count == 50

#         await pilot.press(*["down" for _ in range(0, 50)])
#         await pilot.pause()
#         assert data_table.row_count == 100
#         await pilot.exit(None)
