from typing import Type

import pytest
from textual import on
from textual.app import App, CSSPathType
from textual.driver import Driver
from textual.widgets import Button
from textual.reactive import reactive
from textual.pilot import Pilot

from dyno_viewer.aws.ddb import scan_items
from dyno_viewer.components.query.filter_query import FilterQuery
from dyno_viewer.components.query.key_filter import KeyFilter
from dyno_viewer.components.screens import QueryScreen
from dyno_viewer.db.utils import list_query_history, list_saved_queries
from tests.common import type_commands
from dyno_viewer.components.screens.create_saved_query import CreateSavedQueryScreen
from dyno_viewer.models import QueryParameters, TableInfo


@pytest.fixture
def screen_app():
    class QueryScreenApp(App):
        SCREENS = {"query": QueryScreen}
        db_session = reactive(None)

        def __init__(
            self,
            driver_class: Type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
        ):
            super().__init__(driver_class, css_path, watch_css)

        dyn_query: QueryParameters | None = reactive(None)

        @on(QueryScreen.QueryParametersChanged)
        def parameters_update(self, query_param: QueryScreen.QueryParametersChanged):
            self.dyn_query = query_param.params

    return QueryScreenApp


async def assert_primary_key(pilot: Pilot, ddb_item):
    screen = pilot.app.get_screen("query")
    key_query = screen.query_one(KeyFilter)
    # set pk to customer#test
    await type_commands(["tab" for _ in range(0, 2)], pilot)
    await type_commands([ddb_item["pk"]], pilot)
    assert key_query.query_one("#partitionKey").value == ddb_item["pk"]


async def assert_gsi_primary_key(pilot: Pilot, ddb_item):
    screen = pilot.app.get_screen("query")
    key_query = screen.query_one(KeyFilter)
    # set to gsi 1
    await pilot.press("tab", "down", "down", "enter")
    # set pk to customer#test
    await pilot.press("tab")
    await type_commands([ddb_item["gsipk1"]], pilot)
    assert key_query.query_one("#partitionKey").value == ddb_item["gsipk1"]


async def assert_gsi_sort_key(pilot: Pilot, ddb_item):
    # TODO handle different cond and types
    screen = pilot.app.get_screen("query")
    key_filter = screen.query_one(KeyFilter)
    # attr filter type is string
    assert key_filter.query_one("#attrType").value == "string"
    # cond is ==
    assert key_filter.query_one("#condition").value == "=="
    # set sort key value
    await type_commands(["tab" for _ in range(0, 3)], pilot)
    await type_commands([ddb_item["gsisk1"]], pilot)
    assert key_filter.query_one("#attrValue").value == ddb_item["gsisk1"]
    await type_commands(["tab"], pilot)


async def assert_sort_key(pilot: Pilot, ddb_item):
    screen = pilot.app.get_screen("query")
    key_filter = screen.query_one(KeyFilter)
    # attr filter type is string
    assert key_filter.query_one("#attrType").value == "string"
    # cond is ==
    assert key_filter.query_one("#condition").value == "=="
    # set sort key value
    await type_commands(["tab" for _ in range(0, 3)], pilot)
    await type_commands([ddb_item["sk"]], pilot)
    assert key_filter.query_one("#attrValue").value == ddb_item["sk"]
    await type_commands(["tab"], pilot)


async def assert_filter_one(pilot: Pilot, attr_name, attr_value):
    # add new filter
    screen = pilot.app.get_screen("query")
    await type_commands(["enter"], pilot)
    assert len(screen.query(FilterQuery)) == 1
    filter_query = screen.query_one(FilterQuery)
    # set attr filter name to test
    await type_commands(["tab", "tab", "test"], pilot)
    assert filter_query.query_one("#attr").value == attr_name
    # attr filter type is string
    assert filter_query.query_one("#attrType").value == "string"
    # set attr filter cont to ==
    assert filter_query.query_one("#condition").value == "=="
    # set attr filter value to test1
    await type_commands(["tab" for _ in range(0, 3)], pilot)
    await type_commands(["test1"], pilot)
    assert filter_query.query_one("#attrValue").value == attr_value


async def test_initial_state(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        screen = pilot.app.get_screen("query")
        assert screen.is_current
        assert screen.query_one(KeyFilter)
        add_filter_button: Button = screen.query_one("#addFilter")
        assert add_filter_button
        assert str(add_filter_button.label) == "add filter"

        remove_all_filter_button: Button = screen.query_one("#removeAllFilters")
        assert remove_all_filter_button
        assert str(remove_all_filter_button.label) == "remove all filters"


@pytest.mark.skip(reason="flaky look at fixing later. Tested case manually and works")
async def test_add_filter(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        screen = pilot.app.get_screen("query")
        assert screen.is_current
        await type_commands(["tab" for _ in range(0, 6)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = screen.query(FilterQuery)

        assert len(filters) == 2


@pytest.mark.skip(reason="flaky look at fixing later. Tested case manually and works")
async def test_remove_all_filters(screen_app):
    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        await pilot.app.push_screen("query")
        assert screen.is_current
        await type_commands(["tab" for _ in range(0, 6)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 2

        await type_commands(["tab", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 0


async def test_run_query_primary_key(screen_app, ddb_table, ddb_table_with_data):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert screen.is_current
        await assert_primary_key(pilot, ddb_item)
        # run query
        await type_commands(["tab", "r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_condition.partitionKeyValue == ddb_item["pk"]
        assert not dyn_query.key_condition.sortKey
        assert dyn_query.index == "table"

        query_result = query_items(
            ddb_table,
            **dyn_query.boto_params,
        )

        assert query_result


async def test_run_query_primary_key_sort_key(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert screen.is_current

        await assert_primary_key(pilot, ddb_item)
        await assert_sort_key(pilot, ddb_item)

        await type_commands(["r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_condition.partitionKeyValue == ddb_item["pk"]
        assert dyn_query.key_condition.sortKey.attrValue == ddb_item["sk"]
        assert dyn_query.index == "table"

        query_result = query_items(
            ddb_table,
            **dyn_query.boto_params,
        )

        assert query_result


async def test_run_query_primary_key_sort_key_gsi(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert screen.is_current

        await assert_gsi_primary_key(pilot, ddb_item)
        await assert_gsi_sort_key(pilot, ddb_item)

        await type_commands(["r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_condition.partitionKeyValue == ddb_item["gsipk1"]
        assert dyn_query.key_condition.sortKey.attrValue == ddb_item["gsisk1"]
        assert dyn_query.index == "gsi1Index"

        query_result = query_items(
            ddb_table,
            **dyn_query.boto_params,
        )

        assert query_result


async def test_run_query_primary_key_sort_key_filters(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )

        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert screen.is_current
        await assert_primary_key(pilot, ddb_item)
        await assert_sort_key(pilot, ddb_item)
        await assert_filter_one(pilot, "test", "test1")

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query

        query_result = query_items(
            ddb_table,
            **dyn_query.boto_params,
        )

        assert query_result


async def test_run_query_scan(screen_app, ddb_table, ddb_table_with_data):

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )

        await pilot.app.push_screen("query")
        screen = pilot.app.get_screen("query")
        assert screen.is_current
        await pilot.press("enter", "tab", "tab")

        key_filter = screen.query_one(KeyFilter)

        assert key_filter
        assert not key_filter.display

        await assert_filter_one(pilot, "test", "test1")

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.scan_mode
        assert dyn_query.filter_conditions

        query_result = scan_items(
            ddb_table,
            **dyn_query.boto_params,
        )

        assert query_result


async def test_run_query_scan_key_condition_save_query(
    screen_app, ddb_table, ddb_table_with_data, db_session
):

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        pilot.app.db_session = db_session

        await pilot.app.push_screen("query")
        assert screen.is_current

        await assert_primary_key(pilot, ddb_table_with_data[0])
        # send run query message back to root app
        await type_commands(["tab", "s"], pilot)
        await pilot.pause()
        # The screen should still be active since saving is allowed
        assert isinstance(pilot.app.screen, CreateSavedQueryScreen)

        # fill in saved query details
        await type_commands(
            ["test_query_name", "tab", "This is a test saved query."], pilot
        )
        await pilot.click("#create_button")

        await pilot.pause()

        assert isinstance(pilot.app.screen, QueryScreen)
        saved_queries = await list_saved_queries(db_session)

        assert saved_queries
        assert len(saved_queries.items) == 1
        assert saved_queries.items[0].name == "test_query_name"
        assert saved_queries.items[0].description == "This is a test saved query."

        query_params = saved_queries.items[0].to_query_params()
        assert not query_params.scan_mode
        assert (
            query_params.key_condition.partitionKeyValue == ddb_table_with_data[0]["pk"]
        )
        assert not query_params.key_condition.sortKey
        assert not query_params.filter_conditions


async def test_run_query_scan_no_filters(screen_app, ddb_table, ddb_table_with_data):

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )

        await pilot.app.push_screen("query")
        assert screen.is_current
        await pilot.press(
            "enter",
            "tab",
        )

        key_filter = screen.query_one(KeyFilter)

        assert key_filter
        assert not key_filter.display

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query: QueryParameters | None = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.scan_mode
        assert not dyn_query.filter_conditions


async def test_run_query_scan_no_filters_no_save_query(
    db_session, screen_app, ddb_table, ddb_table_with_data
):

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        pilot.app.db_session = db_session

        await pilot.app.push_screen("query")
        assert screen.is_current
        await pilot.press(
            "enter",
            "tab",
        )

        key_filter = screen.query_one(KeyFilter)

        assert key_filter
        assert not key_filter.display

        # send run query message back to root app
        await type_commands(["tab", "s"], pilot)
        await pilot.pause()

        # The screen should still be active since saving is not allowed
        assert isinstance(pilot.app.screen, QueryScreen)


async def test_run_query_scan_no_key_condition_no_save_query(
    db_session, screen_app, ddb_table, ddb_table_with_data
):

    async with screen_app().run_test() as pilot:
        screen = pilot.app.get_screen("query")
        screen.table_info = TableInfo(
            keySchema={"primaryKey": "pk", "sortKey": "sk"},
            gsi={"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
            tableName=ddb_table.name,
        )
        pilot.app.db_session = db_session

        await pilot.app.push_screen("query")
        assert screen.is_current
        await pilot.press(
            # ensure key condition is empty
            "tab",
            "tab",
        )

        key_filter = screen.query_one(KeyFilter)

        assert key_filter
        assert key_filter.display

        # send save query message back to root app
        await type_commands(["tab", "s"], pilot)
        await pilot.pause()

        # The screen should still be active since saving is not allowed
        assert isinstance(pilot.app.screen, QueryScreen)
