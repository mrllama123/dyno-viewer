from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Button,
    Input,
    RadioButton,
    ContentSwitcher,
    OptionList,
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


class KeyQueryInput(Widget):
    index_mode = reactive("table")

    gsi_indexes = reactive({})

    partition_key_attr_name = reactive("")
    sort_key_attr_name = reactive("")

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Horizontal(
                Label("Scan "),
                Switch(name="scan", id="scanToggleSwitch"),
                id="scanToggle",
            ),
            OptionList("table", id="queryIndex"),
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

    def on_option_list_option_selected(self, selected: OptionList.OptionSelected):
        self.index_mode = selected.option.prompt
        if selected.option.prompt != "table":
            self.query_one("#partitionKey").placeholder = self.gsi_indexes[
                selected.option.prompt
            ]["primaryKey"]
            self.query_one("#sortKeyFilter").attr_name = self.gsi_indexes[
                selected.option.prompt
            ]["sortKey"]
            
        else:
            
            self.query_one("#partitionKey").placeholder = self.partition_key_attr_name
            self.query_one("#sortKeyFilter").attr_name = self.sort_key_attr_name

    # watch methods

    def watch_gsi_indexes(self, new_gsi_indexes) -> None:
        if new_gsi_indexes:
            option_list: OptionList = self.query_one("#queryIndex")
            option_list.clear_options()
            for option in ["table", *list(new_gsi_indexes.keys())]:
                option_list.add_option(option)

    def watch_partition_key_attr_name(self, new_partition_key_attr_name) -> None:
        if new_partition_key_attr_name:
            self.query_one("#partitionKey").placeholder = new_partition_key_attr_name

    def watch_sort_key_attr_name(self, sort_key_attr_name) -> None:
        if sort_key_attr_name:
            self.query_one("#sortKeyFilter").attr_name = sort_key_attr_name


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
        yield Input(placeholder="value", id="attrValue")
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
    attr_name = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield Input(value=self.attr_name, id="attr", disabled=True)
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
        yield Input(placeholder="value", id="attrValue")
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
        if new_attr_name:
            self.query_one("#attr").value = new_attr_name
