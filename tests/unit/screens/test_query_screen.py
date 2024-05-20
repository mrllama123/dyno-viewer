from typing import Type

import pytest
from textual.app import App, CSSPathType
from textual.driver import Driver
from textual.widgets import Button

from dyno_viewer.aws.ddb import scan_items
from dyno_viewer.components.query.filter_query import FilterQuery
from dyno_viewer.components.query.key_filter import KeyFilter
from dyno_viewer.components.screens import QueryScreen
from tests.common import type_commands


@pytest.fixture
def screen_app():
    class QueryScreenApp(App):
        SCREENS = {"query": QueryScreen()}

        def __init__(
            self,
            driver_class: Type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
        ):
            self.dyn_query = None
            super().__init__(driver_class, css_path, watch_css)

        async def on_query_screen_run_query(self, run_query):
            self.dyn_query = run_query

    return QueryScreenApp


async def assert_primary_key(pilot, ddb_item):
    key_query = pilot.app.query_one(KeyFilter)
    # set pk to customer#test
    await type_commands(["tab" for _ in range(0, 2)], pilot)
    await type_commands([ddb_item["pk"]], pilot)
    assert key_query.query_one("#partitionKey").value == ddb_item["pk"]


async def assert_gsi_primary_key(pilot, ddb_item):
    key_query = pilot.app.query_one(KeyFilter)
    # set pk to customer#test
    await pilot.press("tab", "down", "enter", "tab")
    await type_commands([ddb_item["gsipk1"]], pilot)
    assert key_query.query_one("#partitionKey").value == ddb_item["gsipk1"]


async def assert_gsi_sort_key(pilot, ddb_item):
    # TODO handle different cond and types
    sort_key = pilot.app.query_one(KeyFilter).query_one("#sortKeyFilter")
    # attr filter type is string
    assert sort_key.query_one("#attrType").value == "string"
    # cond is ==
    assert sort_key.query_one("#condition").value == "=="
    # set sort key value
    await type_commands(["tab" for _ in range(0, 3)], pilot)
    await type_commands([ddb_item["gsisk1"]], pilot)
    assert sort_key.query_one("#attrValue").value == ddb_item["gsisk1"]
    await type_commands(["tab"], pilot)


async def assert_sort_key(pilot, ddb_item):
    # TODO handle different cond and types
    sort_key = pilot.app.query_one(KeyFilter).query_one("#sortKeyFilter")
    # attr filter type is string
    assert sort_key.query_one("#attrType").value == "string"
    # cond is ==
    assert sort_key.query_one("#condition").value == "=="
    # set sort key value
    await type_commands(["tab" for _ in range(0, 3)], pilot)
    await type_commands([ddb_item["sk"]], pilot)
    assert sort_key.query_one("#attrValue").value == ddb_item["sk"]
    await type_commands(["tab"], pilot)


async def assert_filter_one(pilot, attr_name, attr_value):
    # add new filter
    await type_commands(["enter"], pilot)
    assert len(pilot.app.query(FilterQuery)) == 1
    filter_query = pilot.app.query_one(FilterQuery)
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
        assert pilot.app.SCREENS["query"].is_current
        assert pilot.app.query_one(KeyFilter)
        add_filter_button: Button = pilot.app.query_one("#addFilter")
        assert add_filter_button
        assert str(add_filter_button.label) == "add filter"

        remove_all_filter_button: Button = pilot.app.query_one("#removeAllFilters")
        assert remove_all_filter_button
        assert str(remove_all_filter_button.label) == "remove all filters"


async def test_add_filter(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await type_commands(["tab" for _ in range(0, 6)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 2


async def test_remove_all_filters(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
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
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await assert_primary_key(pilot, ddb_item)
        # run query
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert not dyn_query.filter_cond_exp

        query_result = query_items(
            ddb_table,
            KeyConditionExpression=dyn_query.key_cond_exp,
        )

        assert query_result


async def test_run_query_primary_key_sort_key(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current

        await assert_primary_key(pilot, ddb_item)
        await assert_sort_key(pilot, ddb_item)

        await type_commands(["r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert not dyn_query.filter_cond_exp

        query_result = query_items(
            ddb_table,
            KeyConditionExpression=dyn_query.key_cond_exp,
        )

        assert query_result


async def test_run_query_primary_key_sort_key_gsi(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current

        await assert_gsi_primary_key(pilot, ddb_item)
        await assert_gsi_sort_key(pilot, ddb_item)

        await type_commands(["r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert dyn_query.index == "gsi1Index"
        assert not dyn_query.filter_cond_exp

        query_result = query_items(
            ddb_table,
            IndexName=dyn_query.index,
            KeyConditionExpression=dyn_query.key_cond_exp,
        )

        assert query_result


async def test_run_query_primary_key_sort_key_filters(
    screen_app, ddb_table, ddb_table_with_data
):
    from dyno_viewer.aws.ddb import query_items

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }

        ddb_item = ddb_table_with_data[0]
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await assert_primary_key(pilot, ddb_item)
        await assert_sort_key(pilot, ddb_item)
        await assert_filter_one(pilot, "test", "test1")

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert dyn_query.filter_cond_exp

        query_result = query_items(
            ddb_table,
            KeyConditionExpression=dyn_query.key_cond_exp,
            FilterExpression=dyn_query.filter_cond_exp,
        )

        assert query_result


async def test_run_query_scan(screen_app, ddb_table, ddb_table_with_data):

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }

        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await pilot.press(
            "enter",
            "tab",
        )

        assert not pilot.app.query(KeyFilter)
        await assert_filter_one(pilot, "test", "test1")

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert not dyn_query.key_cond_exp
        assert dyn_query.filter_cond_exp

        query_result = scan_items(
            ddb_table,
            FilterExpression=dyn_query.filter_cond_exp,
        )

        assert query_result


async def test_run_query_scan_no_filters(screen_app, ddb_table, ddb_table_with_data):

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }

        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await pilot.press(
            "enter",
            "tab",
        )

        assert not pilot.app.query(KeyFilter)

        # send run query message back to root app
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert not dyn_query.key_cond_exp
        assert not dyn_query.filter_cond_exp
