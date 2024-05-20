from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label


class ErrorScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(
        self,
        error_msg: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.error_msg = error_msg
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        yield Vertical(Label(self.error_msg), Button("OK"))

    def on_button_pressed(self, _) -> None:
        self.app.pop_screen()
