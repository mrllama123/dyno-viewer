from decimal import Decimal
from textual.screen import ModalScreen
from textual.widgets import Static
import json
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

    def convert_decimal_to_float(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def format_dict(self, item):
        return {k: self.convert_decimal_to_float(v) for k, v in item.items()}

    def compose(self):
        formatted_item = self.format_dict(self.item_payload)
        json_str = json.dumps(formatted_item)
        yield Static(JSON(json_str))
