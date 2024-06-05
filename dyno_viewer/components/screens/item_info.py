from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.widgets import Pretty

class ItemInfo(ModalScreen):
    BINDINGS = {("escape", "app.pop_screen", "exit")}
    item_payload = reactive({})

    def compose(self):

        yield Pretty(self.item_payload)

    def watch_item_payload(self, new_payload):
        if new_payload:
            pretty = self.query_one(Pretty)
            pretty.update(new_payload)

