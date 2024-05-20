from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView

from dyno_viewer.aws.session import get_available_profiles


class ProfileSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class ProfileSelected(Message):
        def __init__(self, profile: str) -> None:
            self.profile = profile
            super().__init__()

    def compose(self) -> ComposeResult:
        yield ListView(
            *[
                ListItem(Label(profile), id=profile)
                for profile in get_available_profiles()
            ],
            id="profiles",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.ProfileSelected(selected.item.id))
        self.app.pop_screen()
