from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Button,
    Input,
    RadioButton,
    ContentSwitcher,
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
                id="scanToggle",
            ),
            # OptionList("table", id="indexSelect"),
            RadioSet(
                "table",
                "gsi1Index",
            ),
            Input(placeholder="pk", id="rangeKey"),
            Input(placeholder="sk", id="sortKey"),
            id="queryInput",
        )

    #  on methods
    def on_switch_changed(self, changed: Switch.Changed) -> None:
        if changed.value:
            for input in self.query(Input):
                input.display = False
        else:
            for input in self.query(Input):
                input.display = True

    def on_radio_button_changed(self, changed: RadioButton.Changed):
        print(changed.radio_button.label)
        if str(changed.radio_button.label) != "table":
            # TODO pass this info from root node
            self.query_one("#rangeKey").placeholder = "gsipk1"
            self.query_one("#sortKey").placeholder = "gsisk1"
        else:
            self.query_one("#rangeKey").placeholder = "pk"
            self.query_one("#sortKey").placeholder = "sk"


class FilterQueryInput(Widget):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="attr", id="attr")
        yield Button("type")
        yield RadioSet(
            "string",
            "number",
            "binary",
            "boolean",
            "map",
            "list",
            "set",
            name="type",
            id="attrType",
        )
        yield Button("condition")
        yield RadioSet(
            "==",
            ">",
            "<",
            "<=",
            ">=",
            "!=",
            "between",
            "in",
            "attribute_exists",
            "attribute_not_exists",
            "attribute_type",
            "begins_with",
            "contains",
            "size",
            name="condition",
            id="condition",
        )
        yield Input(placeholder="value", id="value")

    #  on methods

    def on_mount(self) -> None:
        for radio_set in self.query(RadioSet):
            radio_set.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if str(event.button.label) == "type":
            button = self.query_one("#attrType")
        else:
            button = self.query_one("#condition")
        button.display = False if button.display else True
        self.scroll_visible()
