from textual.app import App, on
from textual.widgets import DataTable
from textual.reactive import reactive

from dyno_viewer.components.table import DataTableManager
from dyno_viewer.components.screens.item_info import ItemInfo


class DataTableManagerApp(App):
    data = reactive([])
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

        return [
            {"pk": "customer#33333", "sk": "CUSTOMER", "testAttr": "testy"},
            {"pk": "customer#33334", "sk": "CUSTOMER", "testAttr": "testy"},
            {"pk": "customer#33335", "sk": "CUSTOMER", "testAttr": "testy"},
            {"pk": "customer#33336", "sk": "CUSTOMER", "testAttr": "testy"},
        ]

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


async def test_data_table_manager_view_single_row():
    data = [
        [
            {"pk": "customer#12345", "sk": "CUSTOMER"},
            {"pk": "customer#54321", "sk": "CUSTOMER"},
        ]
    ]
    app = DataTableManagerApp()
    async with app.run_test() as pilot:
        table = app.query_one(DataTable)

        pilot.app.data = data
        await pilot.pause()

        assert table.row_count == len(data[0])
        table_rows = [table.get_row_at(i) for i in range(0, len(data[0]))]
        assert table_rows == [
            ["customer#12345", "CUSTOMER", None, None, None, None],
            ["customer#54321", "CUSTOMER", None, None, None, None],
        ]

        await pilot.press("i")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ItemInfo)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ItemInfo)


async def test_data_table_manager_cursor_type():
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

        await pilot.press("ctrl+r")
        assert table.cursor_type == "column"
        await pilot.press("ctrl+r")
        assert table.cursor_type == "row"
        await pilot.press("ctrl+r")
        assert table.cursor_type == "cell"


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


async def test_data_table_manager_empty_data():
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

        pilot.app.data = []
        assert table.row_count == 0


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
