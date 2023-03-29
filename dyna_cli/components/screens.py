from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Label,
)
from textual.screen import Screen
from textual.events import Enter
from textual.message import Message
from textual.containers import Vertical
from textual.widgets import Button
from dyna_cli.aws.session import get_all_regions
from dyna_cli.aws.ddb import get_ddb_client
from textual import log
from botocore.exceptions import ClientError


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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class TableSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:

        dyn_client = self.parent.dyn_client
        dynamodb_tables = dyn_client.list_tables()["TableNames"]
        # to fix error msg:
        # ResourceWarning: unclosed <ssl.SSLSocket fd=7, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=6, laddr=('...', 55498), raddr=('...', 443)>
        dyn_client.close()


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