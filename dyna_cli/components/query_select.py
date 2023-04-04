from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Button,
    Input,
    Switch,
    RadioSet,
    Label,
)
from textual.widget import Widget

from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.message import Message
from textual.reactive import reactive
from textual.events import Mount
from textual import log


class QueryInput(Widget):
    index_mode = reactive("")

    gsi_indexes = reactive([])

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Scan "),
                Switch(
                    name="scan",
                ),
                classes="scanToggle",
            ),
            # OptionList("table", id="indexSelect"),
            Input(placeholder="pk", id="rangeKey"),
            Input(placeholder="sk", id="sortKey"),
            classes="queryInput",
        )

    # def on_mount(self):
    #     option_list: OptionList = self.query_one("#indexSelect")
    #     option_list.add_option("gsi1Index")

    #  on methods
    def on_switch_changed(self, changed: Switch.Changed) -> None:
        if changed.value:
            for input in self.query(Input):
                input.display = False
        else:
            for input in self.query(Input):
                input.display = True

    # def on_option_list_option_selected(
    #     self, selected: OptionList.OptionSelected
    # ) -> None:
    #     # TODO pass this info from root node
    #     if selected.option.prompt != "table":
    #         self.query_one("#rangeKey").placeholder = "gsipk1"
    #         self.query_one("#sortKey").placeholder = "gsisk1"
    #     else:
    #         self.query_one("#rangeKey").placeholder = "pk"
    #         self.query_one("#sortKey").placeholder = "sk"

