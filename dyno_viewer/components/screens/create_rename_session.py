from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Input, Markdown


class RenameCreateSessionModal(ModalScreen):
    """Modal screen for creating a new table viewer or renaming a session."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close the modal"),
    ]

    def __init__(self, message: str = "Create New Table Viewer Session") -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Markdown(f"# {self.message}")
        yield Input(
            placeholder="Enter session name",
            validators=Length(minimum=1, failure_description="Name cannot be empty"),
            validate_on=["submitted"],
            id="session_name",
        )

    @on(Input.Submitted, "#session_name")
    def submit_input(self, event: Input.Submitted) -> None:
        session_name = event.input.value.strip()
        if session_name:
            self.dismiss(session_name)
