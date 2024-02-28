from textual.widgets import ListItem, ListView, Label, Switch
from textual.screen import Screen
from textual.message import Message
from textual.containers import Container
from textual.reactive import reactive
from textual import on

from dyno_viewer.app_types import ColToggleTable


class TableOptions(Screen):
    BINDINGS = [("escape", "pop_screen", "Pop screen")]
    table_cols = reactive([])

    class ColToggle(Message):
        def __init__(self, cols_toggled: ColToggleTable) -> None:
            self.col_toggled = cols_toggled
            super().__init__()

    def compose(self):
        with Container(id="tableOptionsScreen"):
            yield Container(
                id="tableColSelect",
                *[
                    Container(
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
                            id="tableColSelect",
                            children=[
                                Label(table_col),
                                Switch(value=True, name=table_col, id=table_col),
                            ],
                        )
                    )

    def action_pop_screen(self):
        col_toggles = []
        for col in self.query("#tableColSelect"):
            for switch in col.query(Switch):
                col_toggles.append({"col_key": switch.id, "enabled": switch.value})
        self.post_message(self.ColToggle(col_toggles))
        self.app.pop_screen()
