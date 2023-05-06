from typing import Type
from textual.app import App, CSSPathType, ComposeResult
from textual import events
from textual.driver import Driver
from dyna_cli.components.screens import QueryScreen
from dyna_cli.components.query.filter_query import FilterQuery
from dyna_cli.components.query.key_query import KeyQuery
from textual.widgets import Input, Button
import pytest
from tests.common import type_commands
from boto3.dynamodb.conditions import ConditionExpressionBuilder


def assert_exp(
    exp,
    condition_expression,
    attribute_name_placeholders,
    attribute_value_placeholders,
    is_key=False,
):
    built_expression = ConditionExpressionBuilder().build_expression(
        exp, is_key_condition=is_key
    )

    assert built_expression.condition_expression == condition_expression
    assert built_expression.attribute_name_placeholders == attribute_name_placeholders
    assert built_expression.attribute_value_placeholders == attribute_value_placeholders


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


async def test_initial_state(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        assert pilot.app.query_one(KeyQuery)
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
        await type_commands(["tab" for _ in range(0, 7)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 2


async def test_remove_all_filters(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await type_commands(["tab" for _ in range(0, 7)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 2

        await type_commands(["tab", "enter"], pilot)

        filters = pilot.app.query(FilterQuery)

        assert len(filters) == 0


async def test_run_query_primary_key(screen_app):
    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        # get to pk input
        await type_commands(["tab" for _ in range(0, 3)], pilot)
        # set pk to customer#test
        await type_commands(["customer#test"], pilot)
        # run query
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert not dyn_query.filter_cond_exp

        assert_exp(
            dyn_query.key_cond_exp,
            condition_expression="#n0 = :v0",
            attribute_name_placeholders={"#n0": "pk"},
            attribute_value_placeholders={":v0": "customer#test"},
            is_key=True,
        )

# TODO once concurrency is enabled add more test cases for all the other conditions 
async def test_run_query_primary_key_sort_key(screen_app):
    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        # set pk to customer#test
        await type_commands(["tab" for _ in range(0, 3)], pilot)
        await type_commands(["customer#test"], pilot)
        # set cond to ==
        await type_commands(["tab", "tab", "enter", "tab", "enter"], pilot)
        # set sort key value
        await type_commands(["tab" for _ in range(0, 7)], pilot)
        await type_commands(["test", "tab"], pilot)

        await type_commands(["r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert not dyn_query.filter_cond_exp

        assert_exp(
            dyn_query.key_cond_exp,
            condition_expression="(#n0 = :v0 AND #n1 = :v1)",
            attribute_name_placeholders={"#n0": "pk", "#n1": "sk"},
            attribute_value_placeholders={
                ":v0": "customer#test",
                ":v1": "test",
            },
            is_key=True,
        )

# TODO once concurrency is enabled add more test cases for all the other conditions 
async def test_run_query_primary_key_sort_key_filters(screen_app):
    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["query"].table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {"gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}},
        }
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        # set pk to customer#test
        await type_commands(["tab" for _ in range(0, 3)], pilot)
        await type_commands(["customer#test"], pilot)
        # set cond to ==
        await type_commands(["tab", "tab", "enter", "tab", "enter"], pilot)
        # set sort key value
        await type_commands(["tab" for _ in range(0, 7)], pilot)
        await type_commands(["test"], pilot)
        # add new filter
        await type_commands(["tab", "enter"], pilot)
        assert len(pilot.app.query(FilterQuery)) == 1
        filter_query = pilot.app.query_one(FilterQuery)
        # set attr filter name to test
        await type_commands(["tab", "tab", "test"], pilot)
        assert filter_query.query_one("#attr").value == "test"
        # set attr filter type to string
        await type_commands(["tab", "enter", "tab", "enter"], pilot)
        assert str(filter_query.query_one("#attrType").pressed_button.label) == "string"
        # set attr filter cont to ==
        await type_commands(["tab" for _ in range(0, 7)], pilot)
        await type_commands(["enter", "tab", "enter"], pilot)
        assert str(filter_query.query_one("#condition").pressed_button.label) == "=="
        # ste attr filter value to test1
        await type_commands(["tab" for _ in range(0, 14)], pilot)
        await type_commands(["test1"], pilot)
        assert filter_query.query_one("#attrValue").value == "test1"
        # run query command
        await type_commands(["tab", "r"], pilot)
        dyn_query = pilot.app.dyn_query
        assert dyn_query
        assert dyn_query.key_cond_exp
        assert dyn_query.filter_cond_exp

        assert_exp(
            dyn_query.key_cond_exp,
            condition_expression="(#n0 = :v0 AND #n1 = :v1)",
            attribute_name_placeholders={"#n0": "pk", "#n1": "sk"},
            attribute_value_placeholders={
                ":v0": "customer#test",
                ":v1": "test",
            },
            is_key=True,
        )

        assert_exp(
            dyn_query.filter_cond_exp,
            condition_expression="#n0 = :v0",
            attribute_name_placeholders={"#n0": "test"},
            attribute_value_placeholders={":v0": "=="},
        )
