from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RadioSet, Select

from dyno_viewer.constants import ATTRIBUTE_TYPES, SORT_KEY_CONDITIONS
from dyno_viewer.models import KeyCondition, SortKeyCondition


class KeyFilter(Widget):
    DEFAULT_CSS = """
    KeyFilter {
        margin: 1 1;
        background: $boost;
        border: heavy grey;
        height: 25;
    }
    #attr {
        margin: 1 1;
    }
    """
    index_mode = reactive("table")

    partition_key_attr_name = reactive("")
    sort_key_attr_name = reactive("", layout=True)

    def get_key_condition(self) -> KeyCondition:
        return KeyCondition(
            # index=self.index_mode,
            partitionKeyValue=self.query_one("#partitionKey").value,
            sortKey=(
                SortKeyCondition(
                    attrType=self.query_one("#attrType").value,
                    attrCondition=self.query_one("#condition").value,
                    attrValue=self.query_one("#attrValue").value,
                )
                if self.sort_key_attr_name and self.query_one("#attrValue").value
                else None
            ),
        )

    def is_valid(self) -> bool:
        """Check if the key condition is valid."""
        return bool(self.query_one("#partitionKey").value)

    def load_key_condition(self, key_condition: KeyCondition) -> None:
        self.query_one("#partitionKey").value = key_condition.partitionKeyValue
        if key_condition.sortKey:
            self.query_one("#attrType").value = key_condition.sortKey.attrType
            self.query_one("#condition").value = key_condition.sortKey.attrCondition
            self.query_one("#attrValue").value = key_condition.sortKey.attrValue

    def compose(self) -> ComposeResult:
        # yield OptionList("table", id="queryIndex")
        yield Input(placeholder="pk", id="partitionKey")
        yield Label(self.sort_key_attr_name, id="attr")
        yield Label("Type")
        yield Select(
            [(line, line) for line in ATTRIBUTE_TYPES],
            prompt="type",
            value="string",
            id="attrType",
        )
        yield Label("Condition")
        yield Select(
            [(line, line) for line in SORT_KEY_CONDITIONS],
            prompt="Condition",
            value="==",
            id="condition",
        )
        yield Input(placeholder="value", id="attrValue")

    #  on methods
    def on_mount(self):
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

    def watch_partition_key_attr_name(self, new_partition_key_attr_name) -> None:
        if new_partition_key_attr_name:
            self.query_one("#partitionKey").placeholder = new_partition_key_attr_name
