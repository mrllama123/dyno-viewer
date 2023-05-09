from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Button, RadioSet


class FilterQuery(Widget):
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