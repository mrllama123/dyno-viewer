from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Button,
    Input,
    Switch,
    Label,
)
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from textual.screen import Screen
from textual.message import Message
from textual.reactive import reactive
from textual import log
from dyna_cli.components.query_select import QueryInput



class QueryScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            QueryInput(),
            Button("add filter", id="addFilter"),
            Button("ok", id="sendQuery"),
        )

    # on methods:
    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     if event.button.id == "addFilter":
                
    #         vertical_scroll: VerticalScroll = self.query_one(VerticalScroll)
    #         vertical_scroll.mount(FilterInput())
    #         vertical_scroll.scroll_visible()
