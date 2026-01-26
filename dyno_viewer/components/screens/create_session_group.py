from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Input, Label, Markdown, Switch


class CreateSessionGroup(ModalScreen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Close the modal"),
    ]
    DEFAULT_CSS = """
    #copy_current_sessions {
        height: 4;
        layout: horizontal;
    }
    """

    def compose(self) -> ComposeResult:
        yield Markdown("# Create New workspace")
        with Container(id="copy_current_sessions"):
            yield Label("Copy current sessions")
            yield Switch(name="copy current sessions", value=False)
        yield Input(
            placeholder="Enter workspace name",
            validators=Length(minimum=1, failure_description="Name cannot be empty"),
            validate_on=["submitted"],
            id="workspace_name",
        )

    @on(Input.Submitted, "#workspace_name")
    def submit_input(self, event: Input.Submitted) -> None:
        workspace_name = event.input.value.strip()
        switch = self.query_exactly_one(Switch)
        copy_current_sessions = switch.value
        if workspace_name:
            self.dismiss((workspace_name, copy_current_sessions))
