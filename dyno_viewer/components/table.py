from textual import log
from textual.widgets import DataTable
from textual.reactive import reactive
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message

from dyno_viewer.app_types import TableInfo


class DataDynTable(DataTable):
    def add_dyn_data(self, table_info: TableInfo, data: list[dict]) -> None:
        """
        add dynamodb table data with keys sorted to always be first
        """
        log("add dynamodb data from table")
        key_schema = table_info["keySchema"]
        gsis = table_info["gsi"]

        gsis_col = [
            key for gsi in gsis.values() for key in [gsi["primaryKey"], gsi["sortKey"]]
        ]
        log.info(f"{len(gsis_col)} gsi cols")

        cols = [key_schema["primaryKey"], key_schema["sortKey"], *gsis_col]
        data_cols = {
            attrKey for item in data for attrKey in item if attrKey not in cols
        }
        log.info(f"{len(data_cols)} other cols")
        cols.extend(data_cols)

        log.info(f"{len(cols)} total cols")

        self.clear(columns=True)
        for col in cols:
            self.add_column(col, key=col)

        log.info("col keys=", [str(col.label) for col in self.columns.values()])

        rows = [[item.get(col) for col in cols] for item in data]
        log.info(f"{len(rows)} total rows")
        self.add_rows(rows)

    def add_dyn_data_existing(self, data: list[dict]) -> None:
        """
        add more data to table that has already been setup with dynamodb table data
        """
        if self.row_count == 0:
            raise ValueError("there must be existing data")

        cols_not_exist = {
            attrKey for item in data for attrKey in item if attrKey not in self.columns
        }

        if cols_not_exist:
            log.info(f"adding cols to existing: {cols_not_exist}")
            for col in list(cols_not_exist):
                self.add_column(col, key=col)

            log.info(f"added cols to existing: {cols_not_exist}")

        rows = [[item.get(col.value) for col in self.columns] for item in data]
        log.info("adding rows to existing")
        self.add_rows(rows)
        log.info("added rows to existing")


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

