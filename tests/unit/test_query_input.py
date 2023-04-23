from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.query_select import KeyQueryInput
from textual.widgets import Input
import pytest
import json


@pytest.fixture()
def app() -> App:
    class QueryInputApp(App):
        def compose(self):
            yield KeyQueryInput()

    return QueryInputApp


async def test_toggle_scan(app):
    async with app().run_test() as pilot:
        await pilot.press("tab")
        await pilot.press("enter")

        query_input: KeyQueryInput = pilot.app.query_one(KeyQueryInput)

        inputs = query_input.query(Input)

        assert len(inputs) == 2

        assert all(input for input in inputs if not input.display)


async def test_gsi_switch(app):
    async with app().run_test() as pilot:
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("enter")

        query_input: KeyQueryInput = pilot.app.query_one(KeyQueryInput)

        inputs = query_input.query(Input)

        assert len(inputs) == 2

        assert all(
            input for input in inputs if input.placeholder in ["gsipk1", "gsisk1"]
        )

        await pilot.press("up")
        await pilot.press("enter")

        assert all(
            input for input in inputs if input.placeholder in ["pk", "sk"]
        )
