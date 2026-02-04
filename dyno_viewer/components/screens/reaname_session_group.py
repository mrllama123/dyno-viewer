from textual import on
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Markdown


class RenameSessionGroup(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Pop screen"),
    ]

    def compose(self):
        yield Markdown("# Rename Session group")
        yield Input(placeholder="Enter new session group name")

    @on(Input.Submitted)
    async def rename_session_group(self, event: Input.Submitted):
        new_name = event.value.strip()
        if new_name:
            self.dismiss(new_name)
