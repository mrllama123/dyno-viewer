from textual.widgets import ListItem, ListView, Label, Switch
from textual.screen import Screen
from textual.message import Message
from textual.containers import Container
from textual.reactive import reactive
from textual import on


class TableOptions(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]
    table_cols = reactive([])

    class TableOptionColToggle(Message):
        def __init__(self, col_key: str, enabled: bool) -> None:
            self.col_key = col_key
            self.enabled = enabled
            super().__init__()

    def compose(self):
        with Container(id="tableOptionsScreen"):
            yield Container(
                id="tableColSelect",
                *[
                    Container(
                        id=f"tableColSelect{table_col}",
                        *[
                            Label(table_col),
                            Switch(value=True, name=table_col, id=table_col),
                        ],
                    )
                    for table_col in self.table_cols
                ],
            )

    def watch_table_cols(self, table_cols):
        if table_cols:
            col_select = self.query("tableColSelect")
            if col_select:
                col_select[0].remove_children()
                for table_col in table_cols:
                    col_select[0].mount(
                        Container(
                            id=f"tableColSelect{table_col}",
                            children=[
                                Label(table_col),
                                Switch(value=True, name=table_col, id=table_col),
                            ],
                        )
                    )
    # @on(Switch.Changed)
    # def on_switch_change(self, changed: Switch.Changed) -> None:
    #     self.post_message(self.TableOptionColToggle(changed.switch.id, changed.value))
