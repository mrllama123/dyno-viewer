from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Label,
)
from textual.screen import Screen
from textual.message import Message
from dyna_cli.aws.session import get_all_regions
from dyna_cli.aws.ddb import get_ddb_client

class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()


    def compose(self) -> ComposeResult:
        dyn_client = get_ddb_client(region_name=self.parent.aws_region)
        dynamodb_tables = dyn_client.list_tables()["TableNames"]

        yield ListView(
            *[ListItem(Label(table), id=table) for table in dynamodb_tables],
            id="dynTablesSelect",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.TableName(selected.item.id))
        self.app.pop_screen()


class RegionSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class RegionSelected(Message):
        """"""

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


class ProfileSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class ProfileSelected(Message):
        """"""

        def __init__(self, profile: str) -> None:
            self.profile = profile
            super().__init__()

    def compose(self) -> ComposeResult:
        profiles = self.parent.profiles
        yield ListView(
            *[ListItem(Label(profile), id=profile) for profile in profiles],
            id="profiles",
        )

    async def on_list_view_selected(self, selected) -> None:
        self.post_message(self.ProfileSelected(selected.item.id))
        self.app.pop_screen()