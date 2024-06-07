from textual.screen import ModalScreen
from textual.widgets import Static
import simplejson as json
from rich.json import JSON


class ItemInfo(ModalScreen):
    BINDINGS = {("escape", "app.pop_screen", "exit")}

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
