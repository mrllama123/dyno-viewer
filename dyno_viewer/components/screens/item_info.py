from textual.screen import ModalScreen
from textual.widgets import Pretty


class ItemInfo(ModalScreen):
    BINDINGS = {("escape", "app.pop_screen", "exit")}

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        item: dict | None = None,
    ) -> None:
        self.item_payload = item
        super().__init__(name, id, classes)

    def compose(self):

        yield Pretty(self.item_payload)

    def watch_item_payload(self, new_payload):
        if new_payload:
            pretty = self.query_one(Pretty)
            pretty.update(new_payload)
