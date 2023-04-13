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
from textual.widgets import Footer
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from textual.screen import Screen
from textual.message import Message
from textual.reactive import reactive
from textual import log
from dyna_cli.components.query_select import QueryInput, FilterQueryInput



class QueryScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield QueryInput()
        yield Button("add filter", id="addFilter")
        yield Button("remove all filters", id="removeAllFilters")


    # on methods:
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "addFilter":
            self.mount(FilterQueryInput())
            self.scroll_visible()
        elif event.button.id == "removeAllFilters":
            for filter in self.query(FilterQueryInput):
                filter.remove()
            self.scroll_visible()
