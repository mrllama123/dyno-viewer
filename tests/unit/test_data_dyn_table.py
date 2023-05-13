from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.table import DataDynTable
import pytest
import json


class DataDynTableApp(App[None]):
    """DataDynTable test app"""

    def __init__(self, data):
        self.data = data
        self.table_info = {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {
                "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"},
                "gsi2Index": {"primaryKey": "gsipk2", "sortKey": "gsisk2"},
                "gsi3Index": {"primaryKey": "gsipk3", "sortKey": "gsisk3"},
            },
        }
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataDynTable()

    def on_mount(self, event: events.Mount) -> None:
        table = self.query_one(DataDynTable)
        table.refresh_data(self.table_info, self.data)
        # table.add_columns(self.data)
        # table.add_rows(self.data)


@pytest.mark.parametrize(
    "data,result",
    [
        (
            [
                {"pk": "customer#12345", "sk": "CUSTOMER"},
                {"pk": "customer#54321", "sk": "CUSTOMER"},
            ],
            [
                ["customer#12345", "CUSTOMER", None, None, None, None, None, None],
                ["customer#54321", "CUSTOMER", None, None, None, None, None, None],
            ],
        ),
        (
            [
                {"pk": "customer#12345", "sk": "CUSTOMER"},
                {"pk": "customer#54321", "sk": "", "testAttr": True},
            ],
            [
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
                ],
                ["customer#54321", "", None, None, None, None, None, None, True],
            ],
        ),
    ],
)
async def test_pk_sk_data(data, result) -> None:
    async with DataDynTableApp(data).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)
        assert table.row_count == len(data)
        table_rows = [table.get_row_at(i) for i in range(0, len(data))]
        assert table_rows == result


@pytest.mark.parametrize(
    "data, result",
    [
        (
            [
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                    "gsipk1": "account#123",
                    "gsisk1": "ACCOUNT",
                },
                {"pk": "customer#54321", "sk": "CUSTOMER"},
            ],
            [
                [
                    "customer#12345",
                    "CUSTOMER",
                    "account#123",
                    "ACCOUNT",
                    None,
                    None,
                    None,
                    None,
                ],
                ["customer#54321", "CUSTOMER", None, None, None, None, None, None],
            ],
        ),
        (
            [
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
            [
                ["customer#12345", "CUSTOMER", None, None, None, None, None, None],
                [
                    "customer#12345",
                    "CUSTOMER",
                    "account#123",
                    "ACCOUNT",
                    "account2#123",
                    "ACCOUNT2",
                    "account3#123",
                    "ACCOUNT3",
                ],
            ],
        ),
        (
            [
                {
                    "pk": "customer#12345",
                    "sk": "CUSTOMER",
                    "gsipk1": "account#123",
                    "gsisk1": "ACCOUNT",
                    "locked": True,
                },
                {"pk": "customer#54321", "sk": "CUSTOMER"},
            ],
            [
                [
                    "customer#12345",
                    "CUSTOMER",
                    "account#123",
                    "ACCOUNT",
                    None,
                    None,
                    None,
                    None,
                    True,
                ],
                [
                    "customer#54321",
                    "CUSTOMER",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ],
            ],
        ),
    ],
)
async def test_pk_sk_gsi_data(data, result) -> None:
    async with DataDynTableApp(data).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)

        assert table.row_count == len(data)

        table_rows = [table.get_row_at(i) for i in range(0, len(data))]
        assert table_rows == result

