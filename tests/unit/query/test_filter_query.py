from textual.app import App, ComposeResult
from textual import events
from textual.pilot import Pilot
from dyna_cli.components.screens import QueryScreen
from dyna_cli.components.query.filter_query import FilterQuery
from textual.widgets import Input, Button, RadioSet
import pytest
import json

from tests.common import type_commands


@pytest.fixture()
def app() -> App:
    class FilterQueryInputApp(App):
        def compose(self):
            yield FilterQuery()

    return FilterQueryInputApp


async def test_initial(app):
    async with app().run_test() as pilot:
        assert pilot.app.query_one("#attr")
        assert pilot.app.query_one("#attrValue")
        assert len(pilot.app.query(RadioSet)) == 2
        assert all(
            radio_set
            for radio_set in pilot.app.query(RadioSet)
            if not radio_set.display
        )
        assert pilot.app.query_one("#attrType")
        assert len(pilot.app.query(Button)) == 3
        all(
            button
            for button in pilot.app.query(Button)
            if str(button.label) in ["remove filter", "condition", "type"]
        )


async def test_inputs(app):
    async with app().run_test() as pilot:
        await type_commands(["tab", "dawnstar"], pilot)

        input_attr = pilot.app.query_one("#attr")
        assert input_attr.value == "dawnstar"

        await type_commands([*["tab" for _ in range(0, 3)], "raven"], pilot)
        input_value = pilot.app.query_one("#attrValue")
        assert input_value.value == "raven"


async def test_display_type(app):
    async with app().run_test() as pilot:
        await type_commands(["tab", "tab", "enter"], pilot)
        assert pilot.app.query_one("#attrType").display
        assert not pilot.app.query_one("#condition").display


async def test_display_condition(app):
    async with app().run_test() as pilot:
        await type_commands(["tab", "tab", "tab", "enter"], pilot)
        assert not pilot.app.query_one("#attrType").display
        assert pilot.app.query_one("#condition").display

# TODO add all cond test cases i.e >=, >, <
@pytest.mark.parametrize(
    "cond", [{"condLabel": "==", "contCommand": ["enter"]}]
)
async def test_conds(app, cond):
    async with app().run_test() as pilot:
        await type_commands(
            [*["tab" for _ in range(0, 3)], "enter", "tab", *cond["contCommand"]], pilot
        )
        condition = pilot.app.query_one("#condition")
        assert str(condition.pressed_button.label) == cond["condLabel"]
