import pytest
from textual import events, on
from textual.app import App, ComposeResult

from dyno_viewer.components.dyn_table import DataDynTable
from textual.reactive import reactive


class DataDynTableApp(App[None]):
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
        yield DataDynTable(id="dataDynTable").data_bind(DataDynTableApp.table_info)

    def on_mount(self) -> None:

        table = self.query_one(DataDynTable)
        table.add_data(self.data)



async def test_primary_keys():
    data = [
        {"pk": "customer#123", "sk": "CUSTOMER"},
        {"pk": "customer#456", "sk": "CUSTOMER"},
    ]
    app = DataDynTableApp(data)
    async with app.run_test() as pilot:
        data_table = pilot.app.query_one(DataDynTable)
        table = data_table.get_table()
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
    app = DataDynTableApp(data)
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


# async def test_extra_data():
#     data = [
#         {"pk": "customer#123", "sk": "CUSTOMER", "testAttr": "test"},
#         {"pk": "customer#456", "sk": "CUSTOMER", "testAttr": "test"},
#         {
#             "pk": "customer#789",
#             "sk": "CUSTOMER",
#             "gsipk1": "gsi1",
#             "gsisk1": "gsi1",
#             "testAttr": "test",
#         },
#     ]
#     app = DataDynTableApp(data)
#     async with app.run_test() as pilot:
#         data_table = pilot.app.query_one(DataDynTable)
#         table = data_table.query_one(DataTable)
#         assert table.row_count == len(data)
#         table_rows = [table.get_row_at(i) for i in range(0, len(data))]
#         assert table_rows == [
#             ["customer#123", "CUSTOMER", None, None, None, None, None, None, "test"],
#             ["customer#456", "CUSTOMER", None, None, None, None, None, None, "test"],
#             [
#                 "customer#789",
#                 "CUSTOMER",
#                 "gsi1",
#                 "gsi1",
#                 None,
#                 None,
#                 None,
#                 None,
#                 "test",
#             ],
#         ]
#         table.clear(columns=True)


# async def test_no_data():
#     data = []
#     app = DataDynTableApp(data)
#     async with app.run_test() as pilot:
#         data_table = pilot.app.query_one(DataDynTable)
#         table = data_table.query_one(DataTable)
#         assert table.row_count == 0
#         table.clear(columns=True)

# async def test_multiple_pages():
#     data_1 = [
#         {"pk": "customer#1", "sk": "CUSTOMER"},
#         {"pk": "customer#2", "sk": "CUSTOMER"},
#         {"pk": "customer#3", "sk": "CUSTOMER"},
#         {"pk": "customer#4", "sk": "CUSTOMER"},
#         {"pk": "customer#5", "sk": "CUSTOMER"},
#         {"pk": "customer#6", "sk": "CUSTOMER"},
#         {"pk": "customer#7", "sk": "CUSTOMER"},
#         {"pk": "customer#8", "sk": "CUSTOMER"},
#         {"pk": "customer#9", "sk": "CUSTOMER"},
#         {"pk": "customer#10", "sk": "CUSTOMER"},
#     ]
#     async with DataDynTableApp(data).run_test() as pilot:
#         data_table = pilot.app.query_one(DataDynTable)
#         table = data_table.query_one(DataTable)
#         assert table.row_count == len(data)
#         assert data_table.table_pages == [0, 1]
#         assert data_table.current_page == 0

#         # Go to the next page
#         table.highlight_next()
#         await pilot.wait_for_idle()
#         assert data_table.current_page == 1

#         # Go back to the previous page
#         table.highlight_previous()
#         await pilot.wait_for_idle()
#         assert data_table.current_page == 0
