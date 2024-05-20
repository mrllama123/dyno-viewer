import pytest
from textual.app import App
from textual.containers import Container

from dyno_viewer.components.query.filter_query import FilterQuery
from tests.common import type_commands


@pytest.fixture()
def app() -> App:
    class FilterQueryInputApp(App):
        def compose(self):
            with Container(id="queryScreen"):
                yield FilterQuery()

    return FilterQueryInputApp


async def test_initial(app):
    async with app().run_test() as pilot:
        assert pilot.app.query_one("#attr")
        assert pilot.app.query_one("#attrValue")
        assert pilot.app.query_one("#attrType").value == "string"
        assert pilot.app.query_one("#condition").value == "=="


async def test_attr_name_value(app):
    async with app().run_test() as pilot:
        await type_commands(["dawnstar"], pilot)

        input_attr = pilot.app.query_one("#attr")
        assert input_attr.value == "dawnstar"

        await type_commands(["tab", "tab", "tab", "raven"], pilot)
        input_value = pilot.app.query_one("#attrValue")
        assert input_value.value == "raven"


@pytest.mark.parametrize(
    "cond",
    [
        {"condLabel": "==", "condCommand": []},
        {"condLabel": ">", "condCommand": ["down"]},
        {"condLabel": "<", "condCommand": ["down", "down"]},
        {"condLabel": "<=", "condCommand": ["down" for _ in range(0, 3)]},
        {"condLabel": ">=", "condCommand": ["down" for _ in range(0, 4)]},
        {"condLabel": "!=", "condCommand": ["down" for _ in range(0, 5)]},
        {"condLabel": "between", "condCommand": ["down" for _ in range(0, 6)]},
        {"condLabel": "in", "condCommand": ["down" for _ in range(0, 7)]},
        {"condLabel": "attribute_exists", "condCommand": ["down" for _ in range(0, 8)]},
        {
            "condLabel": "attribute_not_exists",
            "condCommand": ["down" for _ in range(0, 9)],
        },
        {"condLabel": "attribute_type", "condCommand": ["down" for _ in range(0, 10)]},
        {"condLabel": "begins_with", "condCommand": ["down" for _ in range(0, 11)]},
        {"condLabel": "contains", "condCommand": ["down" for _ in range(0, 12)]},
        {"condLabel": "size", "condCommand": ["down" for _ in range(0, 13)]},
    ],
)
async def test_conds(app, cond):
    async with app().run_test() as pilot:
        await type_commands(
            [*["tab" for _ in range(0, 2)], "enter", *cond["condCommand"], "enter"],
            pilot,
        )
        assert pilot.app.query_one("#condition").value == cond["condLabel"]


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
            ["tab", "enter", *type["typeCommand"], "enter"],
            pilot,
        )
        assert pilot.app.query_one("#attrType").value == type["type"]
