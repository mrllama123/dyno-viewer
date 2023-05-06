from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.query.key_query import KeyQuery
from textual.widgets import Input
import pytest
import json


@pytest.fixture()
def app() -> App:
    class QueryInputApp(App):
        def compose(self):
            yield KeyQuery()

    return QueryInputApp


async def test_toggle_scan(app):
    async with app().run_test() as pilot:
        await pilot.press("tab")
        await pilot.press("enter")

        query_input: KeyQuery = pilot.app.query_one(KeyQuery)

        inputs = query_input.query(Input)

        assert len(inputs) == 2

        assert all(input for input in inputs if not input.display)


async def test_gsi_switch(app):
    async with app().run_test() as pilot:
        query_input: KeyQuery = pilot.app.query_one(KeyQuery)
        query_input.gsi_indexes = {
            "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"}
        }
        query_input.partition_key_attr_name = "pk"
        query_input.sort_key_attr_name = "sk"

        assert query_input.query_one("#queryIndex").option_count == 2

        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("enter")

        assert query_input.query_one("#partitionKey").placeholder == "gsipk1"

        assert query_input.query_one("#sortKeyFilter").attr_name == "gsisk1"

        await pilot.press("up")
        await pilot.press("enter")

        assert query_input.query_one("#partitionKey").placeholder == "pk"
        assert query_input.query_one("#sortKeyFilter").attr_name == "sk"




