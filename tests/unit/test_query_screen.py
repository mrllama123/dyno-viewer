from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.screens import QueryScreen
from dyna_cli.components.query_select import QueryInput, FilterQueryInput
from textual.widgets import Input, Button
import pytest
from tests.common import type_commands


@pytest.fixture
def screen_app():
    class QueryScreenApp(App):
        SCREENS = {"query": QueryScreen()}
    
    return QueryScreenApp

async def test_initial_state(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        assert pilot.app.query_one(QueryInput)
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
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("enter")
        await pilot.press("enter")

        filters = pilot.app.query(FilterQueryInput)

        assert len(filters) == 2


async def test_add_filter(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("query")
        assert pilot.app.SCREENS["query"].is_current
        await type_commands(["tab" for _ in range(0,6)], pilot)
        await type_commands(["enter", "enter"], pilot)

        filters = pilot.app.query(FilterQueryInput)

        assert len(filters) == 2

        await type_commands(["tab", "enter"], pilot)

        filters = pilot.app.query(FilterQueryInput)

        assert len(filters) == 0


