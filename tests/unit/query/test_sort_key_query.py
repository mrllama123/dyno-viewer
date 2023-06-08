from textual.app import App, ComposeResult
from textual import events
from textual.pilot import Pilot
from dyno_viewer.components.screens import QueryScreen
from dyno_viewer.components.query.sort_key_filter import SortKeyFilter
from textual.widgets import Input, Button, RadioSet, Select
import pytest
import json

from tests.common import type_commands


@pytest.fixture()
def app() -> App:
    class SortKeyFilterApp(App):
        def compose(self):
            yield SortKeyFilter()

    return SortKeyFilterApp


async def test_initial(app):
    async with app().run_test() as pilot:
        assert pilot.app.query_one("#attr")
        assert pilot.app.query_one("#attrValue")
        assert pilot.app.query_one("#attrType").value == "string"
        assert pilot.app.query_one("#condition").value == "=="


async def test_sort_key_value(app):
    async with app().run_test() as pilot:
        await type_commands(["tab", "tab", "raven"], pilot)
        input_value = pilot.app.query_one("#attrValue")
        assert input_value.value == "raven"


@pytest.mark.parametrize(
    "type",
    [
        {"type": "string", "typeCommand": []},
        {"type": "number", "typeCommand": ["down"]},
        {"type": "binary", "typeCommand": ["down", "down"]},
        {"type": "boolean", "typeCommand": ["down" for _ in range(0, 3)]},
        {"type": "map", "typeCommand": ["down" for _ in range(0, 4)]},
        {"type": "list", "typeCommand": ["down" for _ in range(0, 5)]},
        {"type": "set", "typeCommand": ["down" for _ in range(0, 6)]},
    ],
)
async def test_types(app, type):
    async with app().run_test() as pilot:
        await type_commands(
            ["enter", *type["typeCommand"], "enter"],
            pilot,
        )
        assert pilot.app.query_one("#attrType").value == type["type"]


@pytest.mark.parametrize(
    "cond",
    [
        {"condLabel": "==", "condCommand": []},
        {"condLabel": ">", "condCommand": ["down"]},
        {"condLabel": "<", "condCommand": ["down", "down"]},
        {"condLabel": "<=", "condCommand": ["down" for _ in range(0, 3)]},
        {"condLabel": ">=", "condCommand": ["down" for _ in range(0, 4)]},
        {"condLabel": "between", "condCommand": ["down" for _ in range(0, 5)]},
        {"condLabel": "begins_with", "condCommand": ["down" for _ in range(0, 6)]},
    ],
)
async def test_conds(app, cond):
    async with app().run_test() as pilot:
        await type_commands(
            ["tab", "enter", *cond["condCommand"], "enter"],
            pilot,
        )
        assert pilot.app.query_one("#condition").value == cond["condLabel"]
