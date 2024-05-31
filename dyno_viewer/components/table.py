from textual import log
from textual.widgets import DataTable
from textual.reactive import reactive
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message

from dyno_viewer.app_types import TableInfo


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
    static_cols = reactive([])
    page_index = reactive(0)

    class PaginateRequest(Message):
        pass

    def _update_table(self, new_page):
        table = self.query_one(DataTable)
        table.clear(columns=True)
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

    def compose(self):
        yield DataTable()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.focus()

    def action_page_decrement(self):
        if self.page_index >= 0:
            self.page_index -= 1

    def action_page_increment(self):
        if self.page_index < len(self.data) - 1:
            self.page_index += 1
        else:
            self.post_message(self.PaginateRequest())
            self.loading = True

    def watch_data(self, new_data):
        # only update first time data is added
        log.info("data updated, updating table", new_data)
        table = self.query_one(DataTable)
        if not new_data and table.row_count > 0:
            table.clear(columns=True)
            return

        if not new_data:
            return

        if len(new_data) == 1:
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

    def watch_page_index(self, new_page: int):
        if self.data:
            self._update_table(new_page)
