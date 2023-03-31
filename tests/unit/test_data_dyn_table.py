from textual.app import App, ComposeResult
from textual import events
from dyna_cli.components.table import DataDynTable
import pytest


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


@pytest.mark.parametrize(
    "data",
    [
        [
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#54321", "sk": "CUSTOMER"},
        ],
        [
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#54321", "sk": ""},
        ],
    ],
)
async def test_pk_sk_data(data) -> None:
    async with DataDynTableApp(data).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)
        assert table.row_count == len(data)
        for i, data_row in enumerate(data):
            assert table.get_row_at(i) == list(data_row.values())


@pytest.mark.parametrize(
    "data",
    [
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
    ],
)
async def test_pk_sk__gsi_data(data) -> None:
    async with DataDynTableApp(data).run_test() as pilot:
        table: DataDynTable = pilot.app.query_one(DataDynTable)
        assert table.row_count == len(data)
        for i, data_row in enumerate(data):
            table_row = table.get_row_at(i)
            table.get_row
            for v  in data_row.values():
                assert v in table_row
