from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RadioSet, Select


class SortKeyFilter(Widget):
    attr_name = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield Label(self.attr_name, id="attr")
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
                    "between",
                    "begins_with",
                ]
            ],
            prompt="Condition",
            value="==",
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
            radio_set.display = not radio_set.display
            self.scroll_visible()
        if str(event.button.label) == "condition":
            radio_set = self.query_one("#condition")
            radio_set.display = not radio_set.display
            self.scroll_visible()

    # watch methods

    def watch_attr_name(self, new_attr_name):
        if new_attr_name:
            self.query_one("#attr").update(new_attr_name)
