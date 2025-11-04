from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView

from dyno_viewer.aws.session import get_available_profiles


class ProfileSelectScreen(ModalScreen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class ProfileSelected(Message):
        def __init__(self, profile: str) -> None:
            self.profile = profile
            super().__init__()

    def compose(self) -> ComposeResult:
        yield ListView(
            *[ListItem(Label(profile)) for profile in get_available_profiles()],
            id="profiles",
        )

    async def on_list_view_selected(self, selected: ListView.Selected) -> None:

        self.dismiss(str(selected.item.children[0].content))
