from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown


class ConfirmDialogue(ModalScreen):
    """A confirmation dialogue screen."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close dialogue"),
        Binding("y", "confirm", "Confirm action"),
    ]

    DEFAULT_CSS = """
    #dialogue_container {
        layout: grid;
        grid-size: 2 2;
        align: center bottom;
        background: $boost;
    }

    #dialogue_container > Markdown {
        margin: 1;
        text-align: center;
        column-span: 2;
        width: 1fr;
    }

    #dialogue_container > Button {
        margin: 2;
        width: 1fr;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self):
        with Container(id="dialogue_container"):
            yield Markdown(f"# {self.message}", id="confirm_title")
            # with Container(id="confirm_actions"):
            yield Button("Yes", id="confirm_yes", variant="success")
            yield Button("No", id="confirm_no")

    def action_confirm(self) -> None:
        """Action to confirm the dialogue."""
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "confirm_yes":
            self.dismiss(True)
        else:
            self.dismiss(False)
