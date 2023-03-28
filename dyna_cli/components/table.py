from textual.widgets import (
    DataTable,
)

class DataDynTable(DataTable):
    def add_columns(self, dyn_data: list[dict]) -> list[any]:
        cols = {attr for item in dyn_data for attr in item.keys()}
        return super().add_columns(*cols)

    def add_rows(self, dyn_data: list[dict]) -> list[any]:
        cols = [str(col.label) for col in self.columns.values()]
        rows = [[item.get(col) for col in cols] for item in dyn_data]
        return super().add_rows(rows)

