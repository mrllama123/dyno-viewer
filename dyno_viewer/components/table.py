from itertools import cycle

import pyclip
from textual import log
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable

from dyno_viewer.components.screens.view_row_item import ViewRowItem
from dyno_viewer.models import TableInfo
from dyno_viewer.util.util import format_output, output_to_csv_str


class DataTableManager(Widget):
    """
    handles pagination and displaying of dynamodb query and scan results
    """

    BINDINGS = [
        Binding(
            "[",
            action="page_decrement",
            description="prev table results",
            show=False,
            tooltip="Go to previous page of table results",
        ),
        Binding(
            "]",
            action="page_increment",
            description="next table results",
            show=False,
            tooltip="Go to next page of table results",
        ),
        Binding("i", action="view_row_item", description="View table row", show=False),
        Binding("ctrl+r", "change_cursor_type", "Change Cursor type", show=False),
        Binding("c", "copy_table_data", "Copy cell", show=False),
    ]
    DEFAULT_CSS = """
    DataTable {
        min-height: 100%;
    }
    """

    table_info = reactive(None)
    data = reactive([])
    static_cols = reactive([])
    page_index = reactive(0)
    cursors = cycle(["column", "row", "cell"])

    class PaginateRequest(Message):
        pass

    def _update_table(self, new_page):
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.refresh()
        non_static_cols = {
            col
            for data_item in self.data[new_page]
            for col in data_item.keys()
            if col not in self.static_cols
        }
        cols = [*self.static_cols, *non_static_cols]
        for col in cols:
            table.add_column(col, key=col)
        rows = [[item.get(col) for col in cols] for item in self.data[new_page]]

        table.add_rows(rows)
        table.refresh()

    def increment_page_index(self):
        if self.page_index < len(self.data) - 1:
            self.page_index += 1
        else:
            self.post_message(self.PaginateRequest())
            self.loading = True

    def decrement_page_index(self):
        if self.page_index > 0:
            self.page_index -= 1

    def compose(self):
        yield DataTable(id="data_table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.focus()

    def action_page_decrement(self):
        self.decrement_page_index()

    def action_page_increment(self):
        self.increment_page_index()

    def action_view_row_item(self):
        if not self.data:
            return

        table = self.query_one(DataTable)
        current_page = self.data[self.page_index]
        cursor_row = table.cursor_row

        selected_row = current_page[cursor_row]

        self.app.push_screen(ViewRowItem(item=selected_row))

    async def action_change_cursor_type(self) -> None:
        query_table = self.query(DataTable)
        if query_table:
            table = query_table[0]
            next_cursor = next(self.cursors)
            self.notify(f"selection mode: {next_cursor}", timeout=1)
            table.cursor_type = next_cursor

    def action_copy_table_data(self) -> None:
        query_table = self.query(DataTable)
        if query_table:
            table = query_table[0]
            if table.row_count > 0:
                if table.cursor_type == "cell":
                    log.info("copying cell")
                    cell = table.get_cell_at(table.cursor_coordinate)
                    if cell is not None:
                        pyclip.copy(format_output(cell))
                elif table.cursor_type == "row":
                    row = table.get_row_at(table.cursor_row)
                    if row:
                        pyclip.copy(output_to_csv_str(row))
                elif table.cursor_type == "column":
                    col = table.get_column_at(table.cursor_column)
                    if col:
                        pyclip.copy(output_to_csv_str(col))

    def watch_data(self, new_data):
        # only update first time data is added
        log.info("data updated, updating table", new_data)
        table = self.query_one(DataTable)
        if not new_data and table.row_count > 0:
            table.clear(columns=True)
            return

        if new_data:
            self._update_table(self.page_index)

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
        self.page_index = min(self.page_index, 0)

    def watch_page_index(self, new_page: int):
        if self.data:
            self._update_table(new_page)
