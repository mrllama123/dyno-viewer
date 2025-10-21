from boto3.dynamodb.conditions import Attr, Key
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Switch

from dyno_viewer.components.query.filter_query import FilterQuery
from dyno_viewer.components.query.key_filter import KeyFilter
from dyno_viewer.components.screens.create_saved_query import CreateSavedQueryScreen
from dyno_viewer.db.utils import add_saved_query
from dyno_viewer.models import QueryParameters, TableInfo


class QueryScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Close screen"),
        (("r", "run_query", "Run Query")),
        ("s", "save_query", "Save Query"),
    ]
    CSS = """
    #queryScreen {
        layout: vertical;
        overflow-y: auto;
    }

    #queryScreen  Select{
        margin: 1 0;

    }
    #queryIndex {
        margin: 1 1;
        height: 4;
    }

    #queryScreen  Button {
        margin: 1 1;

    }
    #scanToggle {
        margin: 0 1;
        height: 4;
    }
    """

    table_info = reactive(None)
    scan_mode = reactive(False)
    index = reactive("table")

    input_query_params = reactive(None)

    class RunQuery(Message):
        """
        custom message to send back to root screen that has all query

        """

        def __init__(
            self,
            key_cond_exp: Key | None = None,
            filter_cond_exp: Attr | None = None,
            index: str = "table",
        ) -> None:
            self.key_cond_exp = key_cond_exp
            self.filter_cond_exp = filter_cond_exp
            self.index = index
            super().__init__()

    class QueryParametersChanged(Message):
        def __init__(self, params: QueryParameters) -> None:
            self.params = params
            super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="queryScreen"):
            yield Horizontal(
                Label("Scan "),
                Switch(name="scan", id="scanToggleSwitch"),
                id="scanToggle",
            )
            yield OptionList(id="queryIndex")
            yield KeyFilter(id="keyFilter")
            yield Button("add filter", id="addFilter")
            yield Button("remove all filters", id="removeAllFilters")
            yield Footer()

    def update_key_schema(self):
        key_query = self.query_exactly_one(KeyFilter)
        key_query.partition_key_attr_name = self.table_info["keySchema"]["primaryKey"]
        key_query.sort_key_attr_name = self.table_info["keySchema"]["sortKey"]

    def update_index_options(self):
        option_list: OptionList = self.query_one("#queryIndex")
        option_list.clear_options()
        for option in ["table", *list(sorted(self.table_info["gsi"].keys()))]:
            option_list.add_option(option)

    def load_query_parameters(self, params: QueryParameters) -> None:
        """Load existing query parameters into the screen"""
        scan_switch: Switch = self.query_one("#scanToggleSwitch")
        scan_switch.value = params.scan_mode
        if params.index and params.index in ["table", *self.table_info["gsi"].keys()]:
            self.index = params.index
            option_list: OptionList = self.query_one("#queryIndex")
            index = [
                i
                for i, option in enumerate(option_list.options)
                if option.prompt == params.index
            ]
            if index:
                option_list.index = index[0]
        key_filter = self.query_one(KeyFilter)
        if params.key_condition:
            key_filter.load_key_condition(params.key_condition)
        for filter_param in params.filter_conditions:
            filter_query = FilterQuery()
            filter_query.load_filter_condition(filter_param)
            self.mount(filter_query)
        self.scroll_visible()

    # action methods

    def action_run_query(self) -> None:
        new_query_params = self.generate_query_parameters()
        self.post_message(self.QueryParametersChanged(new_query_params))
        self.app.pop_screen()

    def generate_query_parameters(self):
        key_filter = self.query_exactly_one(KeyFilter)
        key_condition = key_filter.get_key_condition()
        primary_key_name = (
            self.table_info["keySchema"]["primaryKey"]
            if self.index == "table"
            else self.table_info["gsi"][self.index]["primaryKey"]
        )
        sort_key_name = (
            self.table_info["keySchema"]["sortKey"]
            if self.index == "table"
            else self.table_info["gsi"][self.index]["sortKey"]
        )
        return QueryParameters(
            scan_mode=self.scan_mode,
            primary_key_name=primary_key_name,
            sort_key_name=sort_key_name,
            key_condition=key_condition,
            index=self.index,
            filter_conditions=[
                filter.get_filter_condition() for filter in self.query(FilterQuery)
            ],
        )

    @work
    async def action_save_query(self) -> None:
        key_filter = self.query_exactly_one(KeyFilter)
        if not self.scan_mode and not key_filter.is_valid():
            self.notify("Cannot save query: Invalid key condition.", severity="warning")
            return

        if self.scan_mode and not self.query(FilterQuery):
            self.notify("Cannot save query: No filter conditions.", severity="warning")
            return
        saved_query = await self.app.push_screen_wait(CreateSavedQueryScreen())
        if saved_query:
            query_params = self.generate_query_parameters()
            await add_saved_query(
                self.app.db_session,
                query_params,
                saved_query.name,
                saved_query.description,
            )
            self.notify("Saved query created successfully.", severity="success")

    # on methods:
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "addFilter":
            self.query_one("#queryScreen").mount(FilterQuery())
            self.scroll_visible()
        elif event.button.id == "removeAllFilters":
            for filter in self.query(FilterQuery):
                if filter.id != "sortKeyFilter":
                    filter.remove()
            self.scroll_visible()

    def on_mount(self):
        if self.table_info:
            self.update_key_schema()
            self.update_index_options()
        if self.input_query_params:
            self.load_query_parameters(self.input_query_params)

    @on(Switch.Changed, "#scanToggleSwitch")
    def toggle_scan_mode(self, changed: Switch.Changed) -> None:
        self.scan_mode = changed.value
        key_filter = self.query_one(KeyFilter)
        if changed.value:
            key_filter.display = False
        else:
            key_filter.display = True

    @on(OptionList.OptionSelected, "#queryIndex")
    def gsi_index_update(self, selected: OptionList.OptionSelected):
        self.index_mode = selected.option.prompt
        if selected.option.prompt != "table":
            new_primary_key = self.table_info["gsi"][selected.option.prompt][
                "primaryKey"
            ]
            new_sort_key = self.table_info["gsi"][selected.option.prompt]["sortKey"]
            key_query = self.query_one(KeyFilter)
            key_query.partition_key_attr_name = new_primary_key
            key_query.sort_key_attr_name = new_sort_key
            self.index = selected.option.prompt

    # watcher methods

    def watch_table_info(self, new_table_info: TableInfo) -> None:
        if new_table_info:
            try:
                self.log.info("Updating table info in query screen")
                self.update_index_options()

                self.update_key_schema()
            except NoMatches as e:
                self.log.error(f"Error updating table info: {e}")
                return
            except Exception:
                raise

    def watch_query_params(self, new_query_params: QueryParameters) -> None:
        if new_query_params and self.is_mounted:
            self.load_query_parameters(new_query_params)
