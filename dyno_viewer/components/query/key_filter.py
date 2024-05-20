from textual import on
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, OptionList

from dyno_viewer.components.query.sort_key_filter import SortKeyFilter


class KeyFilter(Widget):
    index_mode = reactive("table")

    gsi_indexes = reactive({})

    partition_key_attr_name = reactive("")
    sort_key_attr_name = reactive("")

    def compose(self) -> ComposeResult:
        yield OptionList("table", id="queryIndex")
        yield Input(placeholder="pk", id="partitionKey")
        yield SortKeyFilter(id="sortKeyFilter")

    #  on methods
    def on_mount(self):
        # select the first value for queryIndex
        option_list = self.query_one("#queryIndex")
        option_list.action_first()
        option_list.action_select()

    @on(OptionList.OptionSelected)
    def gsi_index_update(self, selected: OptionList.OptionSelected):
        self.index_mode = selected.option.prompt
        if selected.option.prompt != "table":
            new_primary_key = self.gsi_indexes[selected.option.prompt]["primaryKey"]
            new_sort_key = self.gsi_indexes[selected.option.prompt]["sortKey"]

            self.log("new_primary_key=", new_primary_key)
            self.log("new_sort_key=", new_sort_key)

            self.query_one("#partitionKey").placeholder = new_primary_key
            self.query_one("#sortKeyFilter").attr_name = new_sort_key

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

            option_list.action_first()
            option_list.action_select()

    def watch_partition_key_attr_name(self, new_partition_key_attr_name) -> None:
        if new_partition_key_attr_name:
            self.query_one("#partitionKey").placeholder = new_partition_key_attr_name

    def watch_sort_key_attr_name(self, sort_key_attr_name) -> None:
        if sort_key_attr_name:
            self.query_one("#sortKeyFilter").attr_name = sort_key_attr_name
