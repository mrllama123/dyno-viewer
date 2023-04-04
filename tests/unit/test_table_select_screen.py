from unittest.mock import MagicMock
import pytest
from textual.app import App, ComposeResult

from textual.reactive import reactive
from textual.widgets import ListView, Input, Label
from fixtures.ddb_tables import create_ddb_table

"""
NOTE: anything in class instantiated outside of __init__ or method does teardown well with pytest e.g
class TestClass(App):
    table_name = ["test"]

TestClass().table_name.append("test2")
if you used the same class in multiple tests in the same dir then it will keep all the previous values from the other tests i.e table_name would be ["test", "test2"] for the second test
"""


@pytest.fixture
def mock_tables(dynamodb):
    print()
    return [
        create_ddb_table(dynamodb, table_name, 2)
        for table_name in [
            "dawnstar",
            "falkreath",
            "markarth",
            "morthal",
            "raven",
            "riften",
            "solitude",
            "whiterun",
            "windhelm",
            "winterhold",
        ]
    ]


@pytest.fixture
def screen_app() -> App:
    from dyna_cli.components.screens.table_select import TableSelectScreen

    class ScreensApp(App):
        SCREENS = {"tableSelect": TableSelectScreen}

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


async def test_select_table(screen_app, mock_tables):
    import boto3

    async with screen_app().run_test() as pilot:
        pilot.app.SCREENS["tableSelect"].dyn_client = boto3.client("dynamodb")
        await pilot.app.push_screen("tableSelect")

        list_view: ListView = pilot.app.query_one(ListView)
        input: Input = pilot.app.query_one(Input)

        assert input.value == ""

        # search dawn
        await pilot.press("tab")
        await pilot.press("d")
        await pilot.press("a")
        await pilot.press("w")
        await pilot.press("n")

        # update list with result
        assert len(list_view.children) == 1

        # add to input
        await pilot.press("tab")
        await pilot.press("enter")
        assert input.value == "dawnstar"

        # send to root node
        await pilot.press("tab")
        await pilot.press("enter")

        assert pilot.app.table_name == "dawnstar"
        await pilot.exit(None)


async def test_select_no_tables(screen_app, dynamodb):
    import boto3

    async with screen_app().run_test() as pilot:
        # fgff = pilot.app.SCREENS["tableSelect"].tables

        # ttt = list(dynamodb.tables.all())
        pilot.app.SCREENS["tableSelect"].dyn_client = boto3.client("dynamodb")
        await pilot.app.push_screen("tableSelect")

        # tttt= pilot.app.SCREENS["tableSelect"].dyn_client.list_tables()

        list_view: ListView = pilot.app.query_one(ListView)
        input: Input = pilot.app.query_one(Input)

        assert input.value == ""

        # search dawn
        await pilot.press("tab")
        await pilot.press("d")
        await pilot.press("a")

        await pilot.press("w")
        await pilot.press("n")

        # update list with result
        assert len(list_view.children) == 0
        await pilot.exit(None)