from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RadioSet, Select

from dyno_viewer.constants import ATTRIBUTE_TYPES, FILTER_CONDITIONS
from dyno_viewer.models import FilterCondition


class FilterQuery(Widget):
    DEFAULT_CSS = """
    FilterQuery  {
        margin: 1  1;
        background: $boost;
        border: heavy grey;
        height: 25;
        overflow-y: auto;
    }
    """

    def __init__(self, filter_condition: FilterCondition | None = None) -> None:
        super().__init__()
        self.input_filter_condition = filter_condition

    def get_filter_condition(self) -> FilterCondition:
        return FilterCondition(
            attrName=self.query_one("#attr").value,
            attrType=self.query_one("#attrType").value,
            attrCondition=self.query_one("#condition").value,
            attrValue=self.query_one("#attrValue").value,
        )

    def load_filter_condition(self, filter_condition: FilterCondition) -> None:
        self.query_one("#attr").value = filter_condition.attrName
        self.query_one("#attrType").value = filter_condition.attrType
        self.query_one("#condition").value = filter_condition.attrCondition
        self.query_one("#attrValue").value = filter_condition.attrValue

    def compose(self) -> ComposeResult:
        yield Input(placeholder="attr", id="attr")
        yield Label("Type")
        yield Select(
            [(line, line) for line in ATTRIBUTE_TYPES],
            prompt="type",
            value="string",
            id="attrType",
        )

        yield Label("Condition")
        yield Select(
            [(line, line) for line in FILTER_CONDITIONS],
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
        if self.input_filter_condition:
            self.load_filter_condition(self.input_filter_condition)

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
