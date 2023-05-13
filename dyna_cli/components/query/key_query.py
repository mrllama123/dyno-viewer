from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Switch, OptionList, Input

from dyna_cli.components.query.sort_key_filter import SortKeyFilter


class KeyQuery(Widget):
    index_mode = reactive("table")

    gsi_indexes = reactive({})

    partition_key_attr_name = reactive("")
    sort_key_attr_name = reactive("")

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Horizontal(
                Label("Scan "),
                Switch(name="scan", id="scanToggleSwitch"),
                id="scanToggle",
            ),
            OptionList("table", id="queryIndex"),
            Input(placeholder="pk", id="partitionKey"),
            SortKeyFilter(id="sortKeyFilter"),
            id="queryInput",
        )

    #  on methods
    def on_switch_changed(self, changed: Switch.Changed) -> None:
        input = self.query_one("#partitionKey")
        sort_key = self.query_one("#sortKeyFilter")
        if changed.value:
            input.display = False
            sort_key.display = False
        else:
            sort_key.display = True
            input.display = True

    def on_option_list_option_selected(self, selected: OptionList.OptionSelected):
        self.index_mode = selected.option.prompt
        if selected.option.prompt != "table":
            self.query_one("#partitionKey").placeholder = self.gsi_indexes[
                selected.option.prompt
            ]["primaryKey"]
            self.query_one("#sortKeyFilter").attr_name = self.gsi_indexes[
                selected.option.prompt
            ]["sortKey"]

        else:
            self.query_one("#partitionKey").placeholder = self.partition_key_attr_name
            self.query_one("#sortKeyFilter").attr_name = self.sort_key_attr_name

    # watch methods

    def watch_gsi_indexes(self, new_gsi_indexes) -> None:
        if new_gsi_indexes:
            option_list: OptionList = self.query_one("#queryIndex")
            option_list.clear_options()
            for option in ["table", *list(new_gsi_indexes.keys())]:
                option_list.add_option(option)

    def watch_partition_key_attr_name(self, new_partition_key_attr_name) -> None:
        if new_partition_key_attr_name:
            self.query_one("#partitionKey").placeholder = new_partition_key_attr_name

    def watch_sort_key_attr_name(self, sort_key_attr_name) -> None:
        if sort_key_attr_name:
            self.query_one("#sortKeyFilter").attr_name = sort_key_attr_name
