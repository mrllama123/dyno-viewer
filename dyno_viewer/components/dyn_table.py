from textual import log, on, work
from textual.widgets import DataTable
from textual.widget import Widget
from textual.app import ComposeResult
from dyno_viewer.app_types import TableInfo
from textual.reactive import reactive


class DataDynTable(Widget):

    table_info: TableInfo | None = reactive(None)
    current_page = reactive(None)
    table_pages = reactive([])

    def compose(self) -> ComposeResult:
        yield DataTable()

    # def add_data(self, data: list[dict]) -> None:
    #     if not self.table_pages:
    #         self.table_pages.append(data)
    #         self.current_page = 0
    #     else:
    #         self.table_pages.append(data)

    @on(DataTable.CellHighlighted)
    async def paginate_dyn_data(self, highlighted: DataTable.CellHighlighted) -> None:
        if highlighted.coordinate.row == highlighted.data_table.row_count - 1:
            # add code to see if there is data to paginate though or send message to get more data added to pages
            pass
