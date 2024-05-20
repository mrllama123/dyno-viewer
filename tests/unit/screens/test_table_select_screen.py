import pytest
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Input, Label, ListView, OptionList

from tests.common import type_commands

"""
NOTE: anything in class instantiated outside of __init__ or method does teardown well with pytest e.g
class TestClass(App):
    table_name = ["test"]

TestClass().table_name.append("test2")
if you used the same class in multiple tests in the same dir then it will keep all the previous values from the other tests i.e table_name would be ["test", "test2"] for the second test
"""


@pytest.fixture
def screen_app() -> App:
    from dyno_viewer.components.screens.table_select import TableSelectScreen

    class ScreensApp(App):
        SCREENS = {"tableSelect": TableSelectScreen()}

        table_name = reactive("")

        def compose(self) -> ComposeResult:
            yield Label("test app")

        async def on_table_select_screen_table_name(
            self,
            new_table_name: TableSelectScreen.TableName,
        ) -> None:
            if self.table_name != new_table_name:
                self.table_name = new_table_name.table

    yield ScreensApp


async def test_select_table(screen_app, ddb_tables):
    import boto3

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["tableSelect"].dyn_client = boto3.client("dynamodb")
        await pilot.app.push_screen("tableSelect")

        table_list: OptionList = pilot.app.query_one(OptionList)
        input: Input = pilot.app.query_one(Input)

        assert input.value == ""

        # search dawn
        await type_commands(["dawn"], pilot)

        # update list with result
        assert table_list.option_count == 1

        # add to input
        await type_commands(["tab", "down", "enter"], pilot)
        assert input.value == "dawnstar"

        # send to root node
        await pilot.press("enter")

        assert pilot.app.table_name == "dawnstar"
        await pilot.exit(None)


async def test_select_no_tables(screen_app, dynamodb):
    import boto3

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["tableSelect"].dyn_client = boto3.client("dynamodb")
        await pilot.app.push_screen("tableSelect")

        list_view: ListView = pilot.app.query_one(OptionList)
        input: Input = pilot.app.query_one(Input)

        assert input.value == ""

        # search dawn
        await type_commands(["dawn"], pilot)

        # update list with result
        assert len(list_view.children) == 0
        await pilot.exit(None)
