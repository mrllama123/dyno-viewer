from textual.message import Message

from dyno_viewer.types import TableInfo


class ErrorException(Message):
    def __init__(self, error: Exception) -> None:
        self.exception = error
        super().__init__()


class UpdateDynDataTable(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


class UpdateDynTableInfo(Message):
    def __init__(self, table_info: TableInfo) -> None:
        self.table_info = table_info
        super().__init__()
