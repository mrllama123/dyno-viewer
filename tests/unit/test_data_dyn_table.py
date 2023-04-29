from typing import Type

from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.table import DataDynTable
import pytest
import json


class DataDynTableApp(App[None]):
    """DataDynTable test app"""

    def __init__(self, data):
        self.data = data
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataDynTable()

    def on_mount(self, event: events.Mount) -> None:
        table = self.query_one(DataDynTable)
        table.add_columns(self.data)
        table.add_rows(self.data)


@pytest.fixture
def app() -> Type[DataDynTableApp]:
    return DataDynTableApp


@pytest.mark.parametrize(
    "data,result",
    [
        (
                [
                    {"pk": "customer#12345", "sk": "CUSTOMER"},
                    {"pk": "customer#54321", "sk": "CUSTOMER"},
                ],
                [["customer#12345", "CUSTOMER"], ["customer#54321", "CUSTOMER"]],
        ),
        (
                [
                    {"pk": "customer#12345", "sk": "CUSTOMER"},
                    {"pk": "customer#54321", "sk": "", "testAttr": True},
                ],
                [["customer#12345", "CUSTOMER", None], ["customer#54321", "", True]],
        ),
    ],
)
async def test_pk_sk_data(app, data, result) -> None:
    async with app(data).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)
        assert table.row_count == len(data)
        table_rows = [table.get_row_at(i) for i in range(0, len(data))]
        assert table_rows == result


# TODO: test broken table is not tearing down data correctly
@pytest.mark.parametrize(
    "data",
    [
        {
            "input": [
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                    "gsipk1": "account#123",
                    "gsisk1": "ACCOUNT",
                },
                {"pk": "customer#54321", "sk": "CUSTOMER"},
            ],
            "result": [
                ["customer#12345", "CUSTOMER", "account#123", "ACCOUNT"],
                ["customer#54321", "CUSTOMER", None, None],
            ],
        },
        {
            "input": [
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                },
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                    "gsipk1": "account#123",
                    "gsisk1": "ACCOUNT",
                    "gsipk2": "account2#123",
                    "gsisk2": "ACCOUNT2",
                    "gsipk3": "account3#123",
                    "gsisk3": "ACCOUNT3",
                },
            ],
            "result": [
                [
                    "customer#12345",
                    "CUSTOMER",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ],
                [
                    "customer#12345",
                    "CUSTOMER",
                    "account#123",
                    "ACCOUNT",
                    "account#123",
                    "ACCOUNT",
                    "account2#123",
                    "ACCOUNT2",
                    "account3#123",
                    "ACCOUNT3",
                ],
            ],
        },
        {
            "input": [
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                    "gsipk1": "account#123",
                    "gsisk1": "ACCOUNT",
                    "locked": True,
                },
                {"pk": "customer#54321", "sk": "CUSTOMER"},
            ],
            "result": [
                [
                    "customer#12345",
                    "CUSTOMER",
                    "account#123",
                    "ACCOUNT",
                    True,
                ],
                [
                    "customer#54321",
                    "CUSTOMER",
                    None,
                    None,
                    None,
                ],
            ],
        },
    ],
)
async def test_pk_sk_gsi_data(app, data) -> None:
    async with app(data["input"]).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)

        assert table.row_count == len(data["input"])

        table_rows = [table.get_row_at(i) for i in range(0, len(data["input"]))]
        assert table_rows == data["result"]


@pytest.mark.parametrize(
    "data",
    [
        [],
        [
            {},
        ],
    ],
)
async def test_empty_data(data) -> None:
    async with App().run_test() as pilot:
        await pilot.app.mount(DataDynTable())
        table = pilot.app.query_one(DataDynTable)
        with pytest.raises(Exception):
            table.add_columns(data)
