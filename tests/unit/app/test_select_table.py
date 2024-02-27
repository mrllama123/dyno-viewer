import pytest


async def test_select_table(ddb_table_with_data):
    from dyno_viewer.app import DynCli
    async with DynCli().run_test(size=(100, 50)) as pilot:
        assert pilot.app.dyn_client
        assert pilot.app.table_name == ""
        await pilot.press("t", "tab", "down", "enter", "enter")
        assert pilot.app.table_client
        assert pilot.app.table_name == "dawnstar"

        data_table = pilot.app.query_one("#dynDataTable")
        await pilot.pause()
        assert data_table.row_count == 50
        await pilot.press("x")


async def test_select_multi_table(ddb_table_with_data):
    from dyno_viewer.app import DynCli
    async with DynCli().run_test(size=(100, 50)) as pilot:
        assert pilot.app.dyn_client
        assert pilot.app.table_name == ""
        await pilot.press("t", "tab", "down", "enter", "enter")

        assert pilot.app.table_client
        assert pilot.app.table_name == "dawnstar"

        data_table = pilot.app.query_one("#dynDataTable")
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
#         assert data_table.row_count == 50get_ddb_client
