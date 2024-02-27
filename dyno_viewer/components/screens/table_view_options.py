from textual.widgets import ListItem, ListView, Label, Switch
from textual.screen import Screen
from textual.message import Message
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive


class TableOptions(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]
    table_cols = reactive([])

    class TableOptionColToggle(Message):
        def __init__(self, col_key: str, enabled: bool) -> None:
            self.col_key = col_key
            self.enabled = enabled
            super().__init__()

    def compose(self):
        yield Horizontal(
            id="tableColSelect",
            *[
                Vertical(
                    Label(table_col),
                    Switch(value=True, name=table_col, id=f"tableColSelect{table_col}"),
                )
                for table_col in self.table_cols
            ],
        )

    def watch_table_cols(self, table_cols):
        if table_cols:
            list_view = self.query("tableColSelect")
            if list_view:
                list_view[0].remove_children()
                for table_col in table_cols:
                    list_view[0].mount(
                        Vertical(
                            Label(table_col),
                            Switch(
                                value=True,
                                name=table_col,
                                id=f"tableColSelect{table_col}",
                            ),
                        )
                    )

    async def on_switch_change(self, name, value):
        self.post_message(self.TableOptionColToggle(name, value))