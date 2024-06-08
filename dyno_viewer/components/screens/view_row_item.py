import pyclip
import simplejson as json
from rich.json import JSON
from textual.screen import ModalScreen
from textual.widgets import Static


class ViewRowItem(ModalScreen):
    BINDINGS = {
        ("escape", "app.pop_screen", "exit"),
        ("c", "copy_row", "copy row item"),
    }

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        item: dict | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.item_payload = item

    def compose(self):
        json_str = json.dumps(self.item_payload)
        yield Static(JSON(json_str))

    def action_copy_row(self):
        pyclip.copy(json.dumps(self.item_payload, indent=2))
