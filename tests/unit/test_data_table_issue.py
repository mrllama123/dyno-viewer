import pytest
from textual import events, on, log
from textual.message import Message

from textual.widget import Widget
from textual.widgets import DataTable
from textual.app import App, ComposeResult
from textual.reactive import reactive

from dyno_viewer.app_types import TableInfo
from datetime import datetime

class DataDynTable(Widget):

    table_info: TableInfo | None = reactive(None)
    current_page = reactive(-1)
    table_pages = reactive([])
    key_cols = reactive([])

    class PaginateTable(Message):
        def __init__(self):
            self.message_id = "paginateQueryRequest"
            super().__init__()

    def compose(self) -> ComposeResult:
        yield DataTable()
        print(datetime.now().isoformat(), f" data: {self.table_pages}")

    def add_data(self, data: list[dict]) -> None:
        self.table_pages.append(data)
        self.current_page = 0

    def get_table(self) -> DataTable:
        return self.query_one(DataTable)

    def watch_table_info(self, new_table: TableInfo) -> None:
        log.info("table_info updated, updating gsi and other key cols for table")
        if not new_table:
            return
        key_schema = new_table["keySchema"]
        gsi = new_table["gsi"]
        gsi_cols = [
            key for gsi in gsi.values() for key in [gsi["primaryKey"], gsi["sortKey"]]
        ]
        log.info(f"{len(gsi_cols)} gsi cols")

        self.key_cols = [key_schema["primaryKey"], key_schema["sortKey"], *gsi_cols]

        log.info(f"{len(self.key_cols)} total cols")

    def watch_current_page(self, new_page: int) -> None:
        if new_page == -1:
            return

        table: DataTable = self.query_one(DataTable)
        log("add dynamodb data from table")

        new_data = self.table_pages[new_page].copy()

        data_cols = {
            attrKey
            for item in new_data
            for attrKey in item
            if attrKey not in self.key_cols
        }
        cols = [*self.key_cols, *data_cols]

        table.clear(columns=True)
        for col in cols:
            table.add_column(col, key=col)

        log.info("col keys=", [str(col.label) for col in table.columns.values()])

        rows = [[item.get(col) for col in cols] for item in new_data]
        log.info(f"{len(rows)} total rows")
        table.add_rows(rows)


    def on_unmount(self) -> None:
        self.table_pages = []
        self.current_page = -1
        print(datetime.now().isoformat(), f" data on unmount: {self.table_pages}")


class TestApp(App[None]):
    """DataDynTable test app"""

    table_info = reactive(
        {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {
                "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"},
                "gsi2Index": {"primaryKey": "gsipk2", "sortKey": "gsisk2"},
                "gsi3Index": {"primaryKey": "gsipk3", "sortKey": "gsisk3"},
            },
        }
    )

    def __init__(self, data):
        self.data = data
        super().__init__()

    def compose(self) -> ComposeResult:

        yield DataDynTable().data_bind(TestApp.table_info)

    def on_mount(self) -> None:
        table = self.query_one(DataDynTable)
        table.add_data(self.data)


async def test_1_primary_keys():
    data = [
        {"pk": "customer#123", "sk": "CUSTOMER"},
        {"pk": "customer#456", "sk": "CUSTOMER"},
    ]
    app = TestApp(data)
    async with app.run_test() as pilot:
        await pilot.pause()
        data_table = pilot.app.query_one(DataDynTable)
        data_table.refresh()
        table = data_table.query_one(DataTable)
        assert table.row_count == len(data)
        table_rows = [table.get_row_at(i) for i in range(0, len(data))]
        assert table_rows == [
            ["customer#123", "CUSTOMER", None, None, None, None, None, None],
            ["customer#456", "CUSTOMER", None, None, None, None, None, None],
        ]


async def test_gsi_keys():
    data = [
        {"pk": "customer#123", "sk": "CUSTOMER", "gsipk1": "gsi1", "gsisk1": "gsi1"},
        {"pk": "customer#456", "sk": "CUSTOMER", "gsipk2": "gsi2", "gsisk2": "gsi2"},
        {"pk": "customer#789", "sk": "CUSTOMER", "gsipk3": "gsi3", "gsisk3": "gsi3"},
    ]
    app = TestApp(data)
    async with app.run_test() as pilot:
        data_table = pilot.app.query_one(DataDynTable)
        table = data_table.get_table()
        assert table.row_count == len(data)
        table_rows = [table.get_row_at(i) for i in range(0, len(data))]
        assert table_rows == [
            ["customer#123", "CUSTOMER", "gsi1", "gsi1", None, None, None, None],
            ["customer#456", "CUSTOMER", None, None, "gsi2", "gsi2", None, None],
            ["customer#789", "CUSTOMER", None, None, None, None, "gsi3", "gsi3"],
        ]
