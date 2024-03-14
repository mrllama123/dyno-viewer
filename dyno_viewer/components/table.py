from textual.coordinate import Coordinate
from textual.errors import DuplicateKeyHandlers
from textual.render import measure
from textual.widgets import (
    DataTable,
)
from textual import log
from textual.reactive import reactive
from textual.widgets._data_table import ColumnKey, CellKey, Column, CellType
from dyno_viewer.app_types import TableInfo
from rich.text import Text


class DataDynTable(DataTable):
    disabled_cols = reactive({})

    def disable_column(self, column_key: ColumnKey | str) -> None:

        col = list(self.get_column(column_key))
        col_index = self.get_column_index(column_key)
        self.disabled_cols[(column_key)] = {
            "col_data": col,
            "index": col_index,
            "width": self.columns[column_key].content_width,
        }
        return super().remove_column(column_key)

    def enable_column(self, column_key: ColumnKey | str) -> None:
        col_data = self.disabled_cols.pop(column_key)

        column_key = (
            ColumnKey(column_key) if isinstance(column_key, str) else column_key
        )

        if column_key in self._column_locations:
            raise DuplicateKeyHandlers(f"The column key {column_key!r} already exists.")
        label = Text(column_key.value)
        column = Column(
            column_key,
            label,
            col_data["width"],
            content_width=col_data["width"],
            auto_width=True,
        )

        self.columns[column_key] = column

        if self._column_locations.contains_value(col_data["index"]):
            # handle the case where the column is being added back in the same location
            for index in range(col_data["index"], len(self._column_locations)):
                col_key = self._column_locations.get_key(index)
                self._column_locations[col_key] = index + 1

        self._column_locations[column_key] = col_data["index"]

        # Update pre-existing rows to account for the new column.
        for row_key in self.rows.keys():
            self._data[row_key][column_key] = CellType
            self._updated_cells.add(CellKey(row_key, column_key))

        self._require_update_dimensions = True
        self.check_idle()
        
        if col_data:
            for row_index, row in enumerate(col_data["col_data"]):
                self.update_cell_at(Coordinate(row_index, col_data["index"]), row, update_width=True)
    
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
        data_cols = set(
            [attrKey for item in data for attrKey in item if attrKey not in cols]
        )
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
            raise Exception("there must be existing data")

        cols_not_exist = set(
            [
                attrKey
                for item in data
                for attrKey in item
                if attrKey not in self.columns
            ]
        )

        if cols_not_exist:
            log.info(f"adding cols to existing: {cols_not_exist}")
            for col in list(cols_not_exist):
                self.add_column(col, key=col)

            log.info(f"added cols to existing: {cols_not_exist}")

        rows = [[item.get(col.value) for col in self.columns.keys()] for item in data]
        log.info(f"adding rows to existing")
        self.add_rows(rows)
        log.info(f"added rows to existing")
