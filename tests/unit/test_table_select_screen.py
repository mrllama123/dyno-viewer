import pytest
from textual.app import App
from dyna_cli.aws.ddb import get_table_client
from textual.reactive import reactive
from textual.widgets import ListView, Input
from fixtures.ddb_tables import create_ddb_table


@pytest.fixture
def mock_tables(dynamodb):
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
def screen_app(mock_tables) -> App:
    from dyna_cli.components.screens.table_select import TableSelectScreen

    class ScreensApp(App[None]):
        SCREENS = {"tableSelect": TableSelectScreen()}

        table_name = reactive("")
        table_client = reactive(None)

        def update_table_client(self):
            if self.table_name != "":
                self.table_client = get_table_client(self.table_name)

        async def on_table_select_screen_table_name(
            self,
            new_table_name: TableSelectScreen.TableName,
        ) -> None:
            if self.table_name != new_table_name:
                self.table_name = new_table_name.table
                self.update_table_client()

    return ScreensApp


async def test_list_tables(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("tableSelect")
        list_view = pilot.app.query_one(ListView)

        assert len(list_view) == 0
        tables = pilot.app.SCREENS["tableSelect"].tables
        assert tables == [
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

async def test_select_table(screen_app):
    async with screen_app().run_test() as pilot:
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






