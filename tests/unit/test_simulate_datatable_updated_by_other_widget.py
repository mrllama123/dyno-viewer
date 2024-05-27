from textual import events
from textual.app import App, on
from textual.widget import Widget
from textual.widgets import DataTable
from textual.reactive import reactive


class DataTableManager(Widget):

    data = reactive(None)
    static_cols = reactive(["pk", "sk"])
    page_index = reactive(-1)

    def compose(self):
        yield DataTable()

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

    def compose(self):
        yield DataTableManager().data_bind(DataTableManagerApp.data)


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
            ["customer#12345", "CUSTOMER"],
            ["customer#54321", "CUSTOMER"],
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
            ["customer#12345", "CUSTOMER", "test"],
            ["customer#54321", "CUSTOMER", "test"],
        ]
