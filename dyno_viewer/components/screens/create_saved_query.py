from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Markdown, Static

from dyno_viewer.db.models import SavedQuery


class CreateSavedQueryScreen(ModalScreen):

    BINDINGS = [
        Binding(key="escape", action="app.pop_screen", description="exit screen"),
        Binding(key="c", action="create_saved_query", description="Create Saved Query"),
    ]

    DEFAULT_CSS = """
    #form {
        height: 23;
        margin: 4 8;
        background: $panel;
        color: $text;
        border: tall $background;
        padding: 1 2;
    }
    #actions {
        width: 100%;
        height: auto;
        dock: bottom;
        layout: horizontal;
    }
    Button {
        margin: 1 2;
    }
    Input {
        margin: 1 2;
    }
    .no_error {
        height: 0;
    }
    .error {
        color: red;
        height: auto;
        margin: 0 3;
    }

    """

    def compose(self) -> ComposeResult:
        # Additional UI components for creating a saved query would go here
        with Container(id="form"):
            yield Markdown("# Create Saved Query:", id="title")
            with Container(id="saved_query_inputs"):
                yield Input(
                    placeholder="Query Name",
                    id="query_name",
                    validators=Length(
                        minimum=1, failure_description="Name cannot be empty"
                    ),
                    validate_on=["blur"],
                )
                yield Static("", id="name_error", classes="no_error")
                yield Input(
                    placeholder="Description",
                    id="query_description",
                )

            with Container(id="actions"):
                yield Button("Create", id="create_button")
                yield Button("Cancel", id="cancel_button")

    @on(Button.Pressed, "#create_button")
    def create_saved_query(self, _: Button.Pressed) -> None:
        return self.submit_saved_query()

    @on(Input.Blurred, "#query_name")
    def validate_query_name(self, event: Input.Blurred) -> None:

        name_error = self.query_one("#name_error", Static)
        if not event.input.is_valid:
            name_error.classes = "error"
            name_error.update(
                ",".join(err for err in event.validation_result.failure_descriptions)
            )

        else:
            name_error.update("")
            name_error.classes = "no_error"

    def action_create_saved_query(self) -> None:
        return self.submit_saved_query()

    def submit_saved_query(self):
        query_name = self.query_one("#query_name", Input)
        query_description = self.query_one("#query_description", Input)
        if not query_name.is_valid:
            return
        self.dismiss(
            SavedQuery(name=query_name.value, description=query_description.value)
        )
