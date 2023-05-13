from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Button, RadioSet, Input


class SortKeyFilter(Widget):
    attr_name = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield Label(self.attr_name, id="attr")
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

    # watch methods

    def watch_attr_name(self, new_attr_name):
        if new_attr_name:
            self.query_one("#attr").update(new_attr_name)
