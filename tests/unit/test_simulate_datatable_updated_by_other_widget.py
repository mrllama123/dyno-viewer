from textual import events
from textual.app import App, on, log
from textual.widget import Widget
from textual.widgets import DataTable
from textual.reactive import reactive
from dyno_viewer.app_types import TableInfo
from textual.binding import Binding
from textual.message import Message


class DataTableManager(Widget):
    """
    handles pagination and displaying of dynamodb query and scan results
    """

    BINDINGS = {
        Binding("[", action="page_decrement", description="prev results", show=True),
        Binding("]", action="page_increment", description="next results", show=True),
    }

    table_info = reactive(None)
    data = reactive([])
    static_cols = reactive(["pk", "sk"])
    page_index = reactive(-1)

    class PaginateRequest(Message):
        pass

    def compose(self):
        yield DataTable()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.focus()

    def action_page_decrement(self):
        if self.page_index > -1:
            self.page_index -= 1

    def action_page_increment(self):
        if self.page_index < len(self.data) - 1:
            self.page_index += 1
        else:
            self.post_message(self.PaginateRequest())
            self.loading = True

    def watch_table_info(self, new_table: TableInfo):
        if not new_table:
            return
        log.info("table_info updated, updating gsi and other key cols for table")

        key_schema = new_table["keySchema"]

        gsi = new_table["gsi"]
        gsi_cols = [
            key for gsi in gsi.values() for key in [gsi["primaryKey"], gsi["sortKey"]]
        ]

        log.info(f"{len(gsi_cols)} gsi cols")

        self.static_cols = [key_schema["primaryKey"], key_schema["sortKey"], *gsi_cols]

        log.info(f"{len(self.static_cols)} total cols")

    def watch_data(self, new_data):
        if new_data and self.page_index == -1:
            self.page_index = 0

    def watch_page_index(self, new_page: int):
        if new_page != -1 and self.data:
            table = self.query_one(DataTable)
            table.clear(columns=True)
            non_static_cols = {
                col
                for data_item in self.data[self.page_index]
                for col in data_item.keys()
                if col not in self.static_cols
            }
            cols = [*self.static_cols, *non_static_cols]
            for col in cols:
                table.add_column(col, key=col)
            rows = [
                [item.get(col) for col in cols] for item in self.data[self.page_index]
            ]

            table.add_rows(rows)


class DataTableManagerApp(App):
    data = reactive(None)
    table_info = reactive(
        {
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {
                "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"},
                "gsi2Index": {"primaryKey": "gsipk2", "sortKey": "gsisk2"},
            },
        }
    )
    paginate_count = reactive(4)

    def run_query(self):
        self.paginate_count -= 1
        if self.paginate_count >= 0:
            return [
                {"pk": "customer#33333", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33334", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33335", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33336", "sk": "CUSTOMER", "testAttr": "testy"},
            ]
        return []

    def compose(self):
        yield DataTableManager().data_bind(
            DataTableManagerApp.data, DataTableManagerApp.table_info
        )

    @on(DataTableManager.PaginateRequest)
    def paginate_data(self):
        data_table_man = self.query_one(DataTableManager)
        query_result = self.run_query()
        if query_result:
            data_table_man.data.append(query_result)
            data_table_man.page_index += 1
        data_table_man.loading = False


async def test_data_table_manager():
    data = [
        [
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#54321", "sk": "CUSTOMER"},
        ]
    ]
    app = DataTableManagerApp()
    async with app.run_test() as pilot:
        pilot.app.data = data
        await pilot.pause()
        table = app.query_one(DataTable)
        assert table.row_count == len(data[0])
        table_rows = [table.get_row_at(i) for i in range(0, len(data[0]))]
        assert table_rows == [
            ["customer#12345", "CUSTOMER", None, None, None, None],
            ["customer#54321", "CUSTOMER", None, None, None, None],
        ]


async def test_data_table_manager_extra_data():
    data = [
        [
            {"pk": "customer#12345", "sk": "CUSTOMER", "testAttr": "test"},
            {"pk": "customer#54321", "sk": "CUSTOMER", "testAttr": "test"},
        ]
    ]
    app = DataTableManagerApp()
    async with app.run_test() as pilot:
        pilot.app.data = data
        await pilot.pause()
        table = app.query_one(DataTable)
        assert table.row_count == len(data[0])
        table_rows = [table.get_row_at(i) for i in range(0, len(data[0]))]
        assert table_rows == [
            ["customer#12345", "CUSTOMER", None, None, None, None, "test"],
            ["customer#54321", "CUSTOMER", None, None, None, None, "test"],
        ]


async def test_data_table_manager_pagination():
    data = [
        [
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#54321", "sk": "CUSTOMER"},
            {"pk": "customer#98765", "sk": "CUSTOMER"},
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#12345", "sk": "CUSTOMER"},
        ]
    ]
    app = DataTableManagerApp()
    async with app.run_test() as pilot:
        pilot.app.data = data
        await pilot.pause()
        table = app.query_one(DataTable)
        assert table.row_count == len(data[0])
        table_rows = [table.get_row_at(i) for i in range(0, len(data[0]))]
        assert table_rows == [
            ["customer#12345", "CUSTOMER", None, None, None, None],
            ["customer#54321", "CUSTOMER", None, None, None, None],
            ["customer#98765", "CUSTOMER", None, None, None, None],
            ["customer#12345", "CUSTOMER", None, None, None, None],
            ["customer#12345", "CUSTOMER", None, None, None, None],
            ["customer#12345", "CUSTOMER", None, None, None, None],
        ]

        await pilot.press("]")
        await pilot.pause(0.7)
