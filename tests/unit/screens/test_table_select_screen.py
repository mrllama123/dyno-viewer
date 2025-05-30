import pytest
from typing import Generator, Any
from textual import work
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Input, Label, ListView, OptionList

from dyno_viewer.components.screens.table_select import TableSelectScreen
from tests.common import type_commands

"""
NOTE: anything in class instantiated outside of __init__ or method does teardown well with pytest e.g
class TestClass(App):
    table_name = ["test"]

TestClass().table_name.append("test2")
if you used the same class in multiple tests in the same dir then it will keep all the previous values from the other tests i.e table_name would be ["test", "test2"] for the second test
"""


@pytest.fixture
def screen_app(dynamodb_client):
    from dyno_viewer.components.screens.table_select import TableSelectScreen

    class ScreensApp(App):

        BINDINGS = [
            ("t", "select_table", "Push Table Select Screen"),
        ]

        table_name = reactive("", recompose=True)
        dyn_client = reactive(dynamodb_client, always_update=True)

        def compose(self) -> ComposeResult:
            yield Label(self.table_name or "No table selected")

        @work
        async def action_select_table(self) -> None:
            result = await self.push_screen_wait(TableSelectScreen())
            if result and self.table_name != result:
                self.table_name = result

    yield ScreensApp


async def test_select_table(screen_app, ddb_tables):

    async with screen_app().run_test() as pilot:
        await pilot.press("t")
        current_screen = pilot.app.screen
        assert isinstance(current_screen, TableSelectScreen)
        input_widget: Input = current_screen.query_one(Input)

        assert input_widget.value == ""
        # search dawn
        await type_commands(["dawn"], pilot)
        await pilot.pause()
        assert input_widget.value == "dawn"

        # add to input
        await type_commands(["tab", "down", "enter"], pilot)
        assert input_widget.value == "dawnstar"

        await pilot.press("enter")

        assert pilot.app.table_name == "dawnstar"
        await pilot.exit(None)


async def test_select_no_tables(screen_app):

    async with screen_app().run_test() as pilot:
        await pilot.press("t")
        current_screen = pilot.app.screen
        assert isinstance(current_screen, TableSelectScreen)
        list_view = current_screen.query_one(OptionList)

        # search dawn
        await type_commands(["dawn"], pilot)

        # update list with result
        assert len(list_view.children) == 0
        await pilot.exit(None)
