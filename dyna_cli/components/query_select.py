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
        yield VerticalScroll(
            Horizontal(
                Label("Scan "),
                Switch(
                    name="scan",
                ),
                id="scanToggle",
            ),
            RadioSet("table", "gsi1Index", id="queryIndex"),
            Input(placeholder="pk", id="partitionKey"),
            SortKeyFilter(id="sortKeyFilter"),
            id="queryInput",
        )

    #  on methods
    def on_switch_changed(self, changed: Switch.Changed) -> None:
        input = self.query_one("#partitionKey")
        sort_key = self.query_one("#sortKeyFilter")
        if changed.value:
            input.display = False
            sort_key.display = False
        else:
            sort_key.display = True
            input.display = True

    def on_radio_set_changed(self, changed: RadioSet.Changed):
        radio_button = changed.radio_set.pressed_button
        if str(radio_button.label) != "table":
            # TODO pass this info from root node
            self.query_one("#partitionKey").placeholder = "gsipk1"
            self.query_one("#sortKeyFilter").attr_name = "gsisk1"
        else:
            
            self.query_one("#partitionKey").placeholder = "pk"
            self.query_one("#sortKeyFilter").attr_name = "sk"


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
        if self.id != "sortKeyFilter":
            yield Button("remove filter", id="removeFilter")

    #  on methods

    def on_mount(self) -> None:
        for radio_set in self.query(RadioSet):
            radio_set.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if str(event.button.label) == "type":
            radio_set = self.query_one("#attrType")
            radio_set.display = False if radio_set.display else True
            self.scroll_visible()
        if str(event.button.label) == "condition":
            radio_set = self.query_one("#condition")
            radio_set.display = False if radio_set.display else True
            self.scroll_visible()
        if event.button.id == "removeFilter":
            self.remove()

 

class SortKeyFilter(Widget):
    attr_name = reactive(None, layout=True)

    def compose(self) -> ComposeResult:
        yield Input(placeholder="attr", id="attr", disabled=self.id == "sortKeyFilter")
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
            "between",
            "begins_with",
            name="condition",
            id="condition",
        )
        yield Input(placeholder="value", id="value")
        if self.id != "sortKeyFilter":
            yield Button("remove filter", id="removeFilter")

    #  on methods

    def on_mount(self) -> None:
        for radio_set in self.query(RadioSet):
            radio_set.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if str(event.button.label) == "type":
            radio_set = self.query_one("#attrType")
            radio_set.display = False if radio_set.display else True
            self.scroll_visible()
        if str(event.button.label) == "condition":
            radio_set = self.query_one("#condition")
            radio_set.display = False if radio_set.display else True
            self.scroll_visible()
        if event.button.id == "removeFilter":
            self.remove()

    # watch methods
    def watch_attr_name(self, new_attr_name: str) -> None:
        self.query_one("#attr").value = new_attr_name


