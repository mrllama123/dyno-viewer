from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RadioSet, Select


class FilterQuery(Widget):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="attr", id="attr")
        yield Label("Type")
        yield Select(
            [
                (line, line)
                for line in [
                    "string",
                    "number",
                    "binary",
                    "boolean",
                    "map",
                    "list",
                    "set",
                ]
            ],
            prompt="type",
            value="string",
            id="attrType",
        )

        yield Label("Condition")
        yield Select(
            [
                (line, line)
                for line in [
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
                ]
            ],
            prompt="Condition",
            value="==",
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
            radio_set.display = not radio_set.display
            self.scroll_visible()
        if str(event.button.label) == "condition":
            radio_set = self.query_one("#condition")
            radio_set.display = not radio_set.display
            self.scroll_visible()
        if event.button.id == "removeFilter":
            self.remove()
