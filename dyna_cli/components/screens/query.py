from textual.app import ComposeResult
from textual.widgets import (
    ListItem,
    ListView,
    Button,
    Input,
    Switch,
    Label,
    RadioSet
)
from textual.widget import Widget
from textual.widgets import Footer
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from textual.screen import Screen
from textual.message import Message
from textual.reactive import reactive
from textual import log
from dyna_cli.components.query_select import KeyQueryInput, FilterQueryInput
from boto3.dynamodb.conditions import Key 
from dyna_cli.aws.ddb import convert_filter_exp_key_cond
from dyna_cli.components.screens.types import QueryResult

class QueryScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        (("r", "run_query", "Run Query")),
    ]

    class QueryMessage(Message):
        """
        custom message to send back to root screen that has all query

        """

        def __init__(
            self, filters: list[FilterQueryInput], primary_key: tuple[str, str], sort_key: FilterQueryInput
        ) -> None:
            primary_key_name, primary_key_value = primary_key
            self.KeyConditionExpression = Key(primary_key_name).eq(primary_key_value)

            if all(radio for radio in sort_key.query(RadioSet) if radio.pressed_button):
                sort_key_name = sort_key.query_one("#attr").value
                sort_key_value = sort_key.query_one("#value").value
                value_type =  sort_key.query_one("#attrType").pressed_button.value
                cond = sort_key.query_one("#condition").pressed_button.value
                self.KeyConditionExpression = self.KeyConditionExpression & convert_filter_exp_key_cond(cond, sort_key_name, )
            
            super().__init__()

    def compose(self) -> ComposeResult:
        yield KeyQueryInput()
        yield Button("add filter", id="addFilter")
        yield Button("remove all filters", id="removeAllFilters")

    def generate_query(self) -> QueryResult:
        key_input = self.query_one(KeyQueryInput)


    # action methods

    def action_run_query(self) -> None:
        # TODO gather all query inputs and construct dynamodb scan or query
        self.app.pop_screen()

    # on methods:
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "addFilter":
            self.mount(FilterQueryInput())
            self.scroll_visible()
        elif event.button.id == "removeAllFilters":
            for filter in self.query(FilterQueryInput):
                if filter.id != "sortKeyFilter":   
                    filter.remove()
            self.scroll_visible()
