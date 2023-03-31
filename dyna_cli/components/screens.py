from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Label,
)
from textual.screen import Screen
from textual.events import Key
from textual.message import Message
from textual.containers import Vertical
from textual.widgets import Button, Input
from dyna_cli.aws.session import get_all_regions
from dyna_cli.aws.ddb import get_ddb_client, list_all_tables
from textual import log
from botocore.exceptions import ClientError
from textual.reactive import reactive


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

    tables = []

    dyn_client = reactive(get_ddb_client())

    next_token = reactive(None)

    class TableName(Message):
        """pass back what table was selected"""

        def __init__(self, table: str) -> None:
            self.table = table
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(Input(placeholder="Search for table"), ListView())

    def update_tables(self):
        if self.next_token:
            dynamodb_tables, next_token = list_all_tables(
                self.dyn_client,
                Limit=10,
                ExclusiveStartTableName=self.next_token,
                paginate=False,
            )
        else:
            dynamodb_tables, next_token = list_all_tables(
                self.dyn_client, Limit=10, paginate=False
            )

        self.next_token = next_token
        self.tables.extend(dynamodb_tables)

    # on methods

    def on_input_changed(self, changed: Input.Changed) -> None:
        # TODO make the matching more smarter
        match_tables = [table for table in self.tables if changed.value in table]

        if len(match_tables) == 0:
            self.update_tables()

        list_view = self.query_one(ListView)
        list_view.clear()
        for matched_table in match_tables:
            list_view.append(ListItem(Label(matched_table), id=matched_table))

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.value in self.tables:
            self.post_message(self.TableName(submitted.value))
            self.app.pop_screen()

    async def on_list_view_selected(self, selected: ListView.Selected) -> None:
        input = self.query_one(Input)
        input.value = selected.item.id

    # watch methods

    async def watch_dyn_client(self, new_dyn_client) -> None:
        self.update_tables()
        list_view = self.query_one(ListView)
        list_view.clear()


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
