from textual import log, on, work
from textual.message import Message
from textual.widgets import DataTable
from textual.widget import Widget
from textual.app import ComposeResult
from dyno_viewer.app_types import TableInfo
from textual.reactive import reactive


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

    def add_data(self, data: list[dict]) -> None:
        if not self.table_pages:
            self.table_pages.append(data)
            self.current_page = 0
        else:
            self.table_pages.append(data)
            self.current_page += 1

    def increment_page(self, highlighted: DataTable.CellHighlighted) -> None:
        cell_row = highlighted.coordinate.row
        row_size = highlighted.data_table.row_count - 1

        valid_upper_index = self.current_page + 1 < len(self.table_pages) - 1

        if cell_row == row_size and valid_upper_index:
            self.current_page += 1
            log.info(f"Incrementing page to {self.current_page}")
        else:
            log.info(f"Cannot increment page to {self.current_page + 1}")

    def decrement_page(self, highlighted: DataTable.CellHighlighted) -> None:
        cell_row = highlighted.coordinate.row
        valid_lower_index = self.current_page - 1 >= 0
        if cell_row == 0 and valid_lower_index:
            self.current_page -= 1
            log.info(f"Decrementing page to {self.current_page}")
        else:
            log.info(f"Cannot decrement page to {self.current_page -1}")

    def send_paginate_request(self, highlighted: DataTable.CellHighlighted):
        cell_row = highlighted.coordinate.row
        row_size = highlighted.data_table.row_count - 1

        valid_upper_index = self.current_page + 1 < len(self.table_pages) - 1
        if cell_row == row_size and not valid_upper_index:
            log.info(
                "hit table pages sending paginate request to main app too see if there is more data to add"
            )
            self.post_message(self.PaginateTable())

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
            attrKey for item in new_data for attrKey in item if attrKey not in self.key_cols
        }
        cols = [*self.key_cols, *data_cols]

        table.clear(columns=True)
        for col in cols:
            table.add_column(col, key=col)

        log.info("col keys=", [str(col.label) for col in table.columns.values()])

        rows = [[item.get(col) for col in cols] for item in new_data]
        log.info(f"{len(rows)} total rows")
        table.add_rows(rows)

    @on(DataTable.CellHighlighted)
    async def paginate_dyn_data(self, highlighted: DataTable.CellHighlighted) -> None:
        if self.current_page == -1 or not self.table_pages:
            log.info("no data added for table skipping")
            return

        self.increment_page(highlighted)
        self.decrement_page(highlighted)
        self.send_paginate_request(highlighted)
