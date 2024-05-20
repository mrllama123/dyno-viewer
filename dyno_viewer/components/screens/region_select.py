from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView

from dyno_viewer.aws.session import get_all_regions


class RegionSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class RegionSelected(Message):
        def __init__(self, region: str) -> None:
            self.region = region
            super().__init__()

    def compose(self) -> ComposeResult:
        yield ListView(
            *[ListItem(Label(region), id=region) for region in get_all_regions()],
            id="regions",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.RegionSelected(selected.item.id))
        self.app.pop_screen()
