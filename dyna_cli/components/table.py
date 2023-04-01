from textual.widgets import (
    DataTable,
)
from textual import log


class DataDynTable(DataTable):
    # TODO need to use config instead on hardcoded values
    PRIMARY_KEY = "pk"
    SORTKEY = "sk"

    GSIS = {f"gsipk{i}": f"gsisk{i}" for i in range(1, 5)}

    ALL_PRIMARY_KEYS = [PRIMARY_KEY, SORTKEY]

    def add_columns(self, dyn_data: list[dict]) -> list[any]:
        cols = {attr for item in dyn_data for attr in item.keys()}

        if len(cols) == 0:
            raise Exception("no col keys found")

        log("gsi's:", self.GSIS)

        for gsipk, gsisk in self.GSIS.items():
            if gsipk in cols:
                self.ALL_PRIMARY_KEYS.append(gsipk)
                self.ALL_PRIMARY_KEYS.append(gsisk)

        log(self.ALL_PRIMARY_KEYS)

        all_cols = [
            *self.ALL_PRIMARY_KEYS,
            *[col for col in cols if col not in self.ALL_PRIMARY_KEYS],
        ]

        log("coll's: ", all_cols)

        return super().add_columns(*all_cols)

    def add_rows(self, dyn_data: list[dict]) -> list[any]:
        cols = [str(col.label) for col in self.columns.values()]
        rows = [[item.get(col) for col in cols] for item in dyn_data]
        return super().add_rows(rows)
