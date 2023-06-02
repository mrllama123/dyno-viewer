from textual.widgets import (
    DataTable,
)
from textual import log
from dyno_viewer.components.types import TableInfo


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
        data_cols = set(
            [attrKey for item in data for attrKey in item if attrKey not in cols]
        )
        log.info(f"{len(data_cols)} other cols")
        cols.extend(data_cols)

        log.info(f"{len(cols)} total cols")

        self.clear(columns=True)
        for col in cols:
            self.add_column(col, key=col)

        log.info("col keys=", [str() for col in self.columns.keys()])

        rows = [[item.get(col) for col in cols] for item in data]
        log.info(f"{len(rows)} total rows")
        self.add_rows(rows)

    def add_dyn_data_existing(self, data: list[dict]) -> None:
        """
        add more data to table that has already been setup with dynamodb table data
        """
        if self.row_count == 0:
            raise Exception("there must be existing data")

        cols_not_exist = [
            attrKey for item in data for attrKey in item if attrKey not in self.columns
        ]
        if cols_not_exist:
            for col in cols_not_exist:
                self.add_column(col, key=col)
        rows = [[item.get(col) for col in self.columns.keys()] for item in data]
        self.add_rows(rows)
