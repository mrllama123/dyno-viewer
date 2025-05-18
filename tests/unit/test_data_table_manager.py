import pytest
from textual.app import App, on
from textual.widgets import DataTable, Footer
from textual.reactive import reactive

from dyno_viewer.components.table import DataTableManager
from dyno_viewer.components.screens.view_row_item import ViewRowItem


class DataTableManagerApp(App):
    data = reactive([])

    paginated_data = reactive(
        [
            [
                {"pk": "customer#33333", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33334", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33335", "sk": "CUSTOMER", "testAttr": "testy"},
                {"pk": "customer#33336", "sk": "CUSTOMER", "testAttr": "testy"},
            ]
        ]
    )
    table_info = reactive(
        {
            "tableName": "test_table_1",
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {
                "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"},
                "gsi2Index": {"primaryKey": "gsipk2", "sortKey": "gsisk2"},
            },
        }
    )

    def run_query(self):
        if not self.paginated_data:
            return None
        return self.paginated_data.pop()

    def compose(self):
        yield DataTableManager().data_bind(
            DataTableManagerApp.data, DataTableManagerApp.table_info
        )
        yield Footer()

    @on(DataTableManager.PaginateRequest)
    def paginate_data(self):
        data_table_man = self.query_one(DataTableManager)
        query_result = self.run_query()
        self.log(f"Paginate data: {query_result}")
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
        table = pilot.app.query_one(DataTable)
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
        table = pilot.app.query_one(DataTable)

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
        assert isinstance(pilot.app.screen, ViewRowItem)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ViewRowItem)


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
        table = pilot.app.query_one(DataTable)
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
        table = pilot.app.query_one(DataTable)
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


@pytest.mark.skip(
    reason="For some reason when you run this test with the rest of the tests it fails but not when run alone. Need to investigate."
)
async def test_data_table_manager_paginate_then_simulate_table_change():
    initial_app_data = [
        [
            {"pk": "new#A", "sk": "NEW_DATA", "extraAttr": "valueA"},
            {"pk": "new#B", "sk": "NEW_DATA", "extraAttr": "valueB"},
        ]
    ]

    new_app_data = [
        [
            {"pk": "store#2231432", "sk": "STORE"},
            {"pk": "store#2231433", "sk": "STORE"},
            {"pk": "store#2231434", "sk": "STORE"},
            {"pk": "store#2231435", "sk": "STORE"},
            {"pk": "store#2231436", "sk": "STORE"},
            {"pk": "store#2231437", "sk": "STORE"},
        ]
    ]
    new_paginated_data = [
        [
            {"pk": "cart#2231432", "sk": "CART"},
            {"pk": "cart#2231433", "sk": "CART"},
            {"pk": "cart#2231434", "sk": "CART"},
            {"pk": "cart#2231435", "sk": "CART"},
            {"pk": "cart#2231436", "sk": "CART"},
            {"pk": "cart#2231437", "sk": "CART"},
        ],
    ]
    expected_rows_after_pagination = [
        ["customer#33333", "CUSTOMER", None, None, None, None, "testy"],
        ["customer#33334", "CUSTOMER", None, None, None, None, "testy"],
        ["customer#33335", "CUSTOMER", None, None, None, None, "testy"],
        ["customer#33336", "CUSTOMER", None, None, None, None, "testy"],
    ]

    # app = DataTableManagerApp()
    async with DataTableManagerApp().run_test() as pilot:
        # Set initial data
        pilot.app.data = initial_app_data
        await pilot.pause()
        table = pilot.app.query_one(DataTable)
        data_table_manager = pilot.app.query_one(DataTableManager)

        assert table.row_count == len(initial_app_data[0])
        actual_initial_rows = [table.get_row_at(i) for i in range(table.row_count)]
        assert actual_initial_rows == [
            ["new#A", "NEW_DATA", None, None, None, None, "valueA"],
            ["new#B", "NEW_DATA", None, None, None, None, "valueB"],
        ]

        # Simulate pagination
        await pilot.press("]")
        await pilot.pause(0.7)  # Wait for pagination processing
        # pilot.app.save_screenshot()
        assert data_table_manager.page_index == 1
        assert table.row_count == len(expected_rows_after_pagination)
        actual_rows_after_pagination = [
            table.get_row_at(i) for i in range(table.row_count)
        ]
        assert actual_rows_after_pagination == expected_rows_after_pagination

        # simulate a table change
        pilot.app.data = []
        # for some reason if i don't copy the data it changes the original data
        pilot.app.paginated_data = new_paginated_data.copy()
        pilot.app.table_info = {
            "tableName": "test_table_2",
            "keySchema": {"primaryKey": "pk", "sortKey": "sk"},
            "gsi": {
                "gsi1Index": {"primaryKey": "gsipk1", "sortKey": "gsisk1"},
                "gsi2Index": {"primaryKey": "gsipk2", "sortKey": "gsisk2"},
            },
        }

        await pilot.pause(0.7)
        assert data_table_manager.page_index == 0  # Page index should reset
        pilot.app.data = new_app_data

        # Verify table reflects the new data and pagination is reset
        assert table.row_count == len(new_app_data[0])
        actual_rows_after_reset = [table.get_row_at(i) for i in range(table.row_count)]
        assert actual_rows_after_reset == [
            ["store#2231432", "STORE", None, None, None, None],
            ["store#2231433", "STORE", None, None, None, None],
            ["store#2231434", "STORE", None, None, None, None],
            ["store#2231435", "STORE", None, None, None, None],
            ["store#2231436", "STORE", None, None, None, None],
            ["store#2231437", "STORE", None, None, None, None],
        ]

        await pilot.press("]")
        await pilot.pause(0.7)  # Wait for pagination processing
        assert data_table_manager.page_index == 1
        assert table.row_count == len(new_paginated_data[0])
        actual_rows_after_new_pagination = [
            table.get_row_at(i) for i in range(table.row_count)
        ]
        assert actual_rows_after_new_pagination == [
            ["cart#2231432", "CART", None, None, None, None],
            ["cart#2231433", "CART", None, None, None, None],
            ["cart#2231434", "CART", None, None, None, None],
            ["cart#2231435", "CART", None, None, None, None],
            ["cart#2231436", "CART", None, None, None, None],
            ["cart#2231437", "CART", None, None, None, None],
        ]
