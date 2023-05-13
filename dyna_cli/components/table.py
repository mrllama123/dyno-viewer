from textual.widgets import (
    DataTable,
)
from textual import log
from dyna_cli.components.types import TableInfo


class DataDynTable(DataTable):
    # TODO need to use config instead on hardcoded values
    PRIMARY_KEY = "pk"
    SORTKEY = "sk"

    GSIS = {f"gsipk{i}": f"gsisk{i}" for i in range(1, 5)}

    ALL_PRIMARY_KEYS = [PRIMARY_KEY, SORTKEY]

    def refresh_data(self, table_info: TableInfo, data: list[dict]) -> None:
        log("reafresh data for table")
        key_schema = table_info["keySchema"]
        gsis = table_info["gsi"]

        gsis_col = [
            key for gsi in gsis.values() for key in [gsi["primaryKey"], gsi["sortKey"]]
        ]
        log.info(f"{len(gsis_col)} gsi cols")

        cols = [key_schema["primaryKey"], key_schema["sortKey"], *gsis_col]
        data_cols = [
            attrKey for item in data for attrKey in item if attrKey not in cols
        ]
        log.info(f"{len(data_cols)} other cols")
        cols.extend(data_cols)

        log.info(f"{len(cols)} total cols")

        self.clear()
        for col in cols:
            self.add_column(col, key=col)

        rows = [[item.get(col) for col in cols] for item in data]
        log.info(f"{len(rows)} total rows")
        super().add_rows(rows)

    def add_data(self, data: list[dict]) -> None:
        cols_not_exisit = [
            attrKey for item in data for attrKey in item if attrKey not in self.columns
        ]
        if cols_not_exisit:
            for col in cols_not_exisit:
                self.add_column(col, key=col)
        rows = [[item.get(col) for col in self.columns.keys()] for item in data]
        super().add_rows(rows)
