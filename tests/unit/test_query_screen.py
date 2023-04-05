from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.screens import QueryScreen
from dyna_cli.components.query_select import QueryInput, FilterQueryInput
from textual.widgets import Input, Button
import pytest
import json


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
        button: Button = pilot.app.query_one(Button)
        assert button
        assert str(button.label) == "add filter"
        assert button.id == "addFilter"


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



