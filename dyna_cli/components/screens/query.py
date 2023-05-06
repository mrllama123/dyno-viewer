from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.widgets import ListItem, ListView, Button, Input, Switch, Label, RadioSet
from textual.widget import Widget
from textual.widgets import Footer
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from textual.screen import Screen
from textual.message import Message
from textual.reactive import reactive
from textual import log
from dyna_cli.components.query_select import KeyQueryInput, FilterQueryInput
from boto3.dynamodb.conditions import Key, Attr
from dyna_cli.aws.ddb import (
    convert_filter_exp_key_cond,
    convert_filter_exp_attr_cond,
    convert_filter_exp_value,
)


class QueryScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
        (("r", "run_query", "Run Query")),
    ]

    table_info = reactive(None)

    class RunQuery(Message):
        """
        custom message to send back to root screen that has all query

        """

        def __init__(
            self,
            key_cond_exp: Key | None,
            filter_cond_exp: Attr | None,
            index: str | None,
        ) -> None:
            self.key_cond_exp = key_cond_exp
            self.filter_cond_exp = filter_cond_exp
            self.index = index
            super().__init__()

    def compose(self) -> ComposeResult:
        yield KeyQueryInput()
        yield Button("add filter", id="addFilter")
        yield Button("remove all filters", id="removeAllFilters")

    def get_key_query(self) -> Key | None:
        key_input = self.query_one(KeyQueryInput)
        primary_key_name = key_input.partition_key_attr_name
        primary_key_value = key_input.query_one("#partitionKey").value

        if not primary_key_value:
            return

        sort_key = key_input.query_one("#sortKeyFilter")
        sort_key_name = sort_key.attr_name
        sort_key_value = sort_key.query_one("#attrValue").value
        cond = str(
            getattr(sort_key.query_one("#condition").pressed_button, "label", "")
        )
        if sort_key_value:
            return Key(primary_key_name).eq(
                primary_key_value
            ) & convert_filter_exp_key_cond(cond, sort_key_name, sort_key_value)
        return Key(primary_key_name).eq(primary_key_value)

    def get_filter_queries(self) -> Attr | None:
        exp = None

        for filter in self.query(FilterQueryInput):
            attr_name = filter.query_one("#attr").value
            attr_type = str(
                getattr(filter.query_one("#attrType").pressed_button, "label", "")
            )
            attr_value = str(
                getattr(filter.query_one("#condition").pressed_button, "label", "")
            )
            cond = str(
                getattr(filter.query_one("#condition").pressed_button, "label", "")
            )
            if exp:
                exp = exp & convert_filter_exp_attr_cond(
                    cond, attr_name, convert_filter_exp_value(attr_value, attr_type)
                )
            else:
                exp = convert_filter_exp_attr_cond(
                    cond, attr_name, convert_filter_exp_value(attr_value, attr_type)
                )
        return exp

    def update_key_schema(self, key_query):
        key_query.partition_key_attr_name = self.table_info["keySchema"]["primaryKey"]
        key_query.sort_key_attr_name = self.table_info["keySchema"]["sortKey"]
        key_query.gsi_indexes = self.table_info["gsi"]

    # action methods

    def action_run_query(self) -> None:
        key_cond_exp = self.get_key_query()
        filter_cond_exp = self.get_filter_queries()
        index_mode = self.query_one(KeyQueryInput).index_mode
        if key_cond_exp:
            self.post_message(
                self.RunQuery(
                    key_cond_exp,
                    filter_cond_exp,
                    None if index_mode == "table" else index_mode,
                )
            )
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

    def on_mount(self):
        if self.table_info:
            key_query = self.query_one(KeyQueryInput)
            self.update_key_schema(key_query)

    # watcher methods

    def watch_table_info(self, new_table_info) -> None:
        if new_table_info:
            try:
                key_query = self.query_one(KeyQueryInput)
                self.update_key_schema(key_query)
            except NoMatches:
                return
            except Exception:
                raise
