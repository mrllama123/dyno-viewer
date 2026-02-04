from textual import on, work
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Markdown, OptionList
from textual.widgets.option_list import Option

from dyno_viewer.components.screens.reaname_session_group import RenameSessionGroup
from dyno_viewer.models import SelectedSessionGroup, SessionGroup


class SelectSessionGroup(ModalScreen):

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close the modal"),
        Binding("n", "next_page", "Next page"),
        Binding("r", "rename_session_group", "Rename Session Group"),
        Binding("d", "delete_session_group", "Delete Session Group"),
    ]
    HELP = """
    ## Select Session Group 
    """
    page = reactive(1)
    session_groups: dict[str, SessionGroup] = reactive({})
    last_page = reactive(False)

    def compose(self):
        yield Markdown("# Select a Session Group")
        yield Input(placeholder="Search for a session group")
        yield OptionList()
        yield Button("No Session group")

    async def on_mount(self):
        self.update_workspaces()

    @on(Input.Submitted)
    async def on_search_saved_queries(self, event: Input.Submitted) -> None:
        search_name = event.value.strip()
        self.update_workspaces(search_name, clear=True)

    @on(OptionList.OptionSelected)
    async def on_workspace_selected(self, event: OptionList.OptionSelected):
        self.dismiss(
            SelectedSessionGroup(session_group=self.session_groups[event.option_id])
        )

    @on(Button.Pressed)
    async def on_no_workspace(self, _event: Button.Pressed):
        self.dismiss(SelectedSessionGroup())

    @work(exclusive=True)
    async def update_workspaces(self, search_name: str = "", clear: bool = False):
        if self.last_page:
            return
        option_list = self.query_exactly_one(OptionList)
        option_list.loading = True
        if clear:
            self.page = 1
            option_list.clear_options()
        result = await self.app.db_manager.list_session_group(
            page=self.page, page_size=40, search_name=search_name
        )
        if len(result) == 0:
            option_list.loading = False
            self.last_page = True
            return
        self.page += 1
        self.session_groups.update(
            {item.data.session_group_id: item.data for item in result}
        )
        option_list.add_options(
            [Option(item.data.name, item.data.session_group_id) for item in result]
        )
        option_list.loading = False

    async def action_next_page(self):
        if self.app.session_group:
            return
        if self.last_page:
            return
        search_input = self.query_exactly_one(Input)
        self.update_workspaces(search_input.value)

    @work
    async def action_rename_session_group(self):
        option_list = self.query_exactly_one(OptionList)
        if not option_list.highlighted_option:
            return
        option = option_list.highlighted_option
        new_name = await self.app.push_screen_wait(RenameSessionGroup())
        if not new_name:
            return
        updated_session_group = await self.app.db_manager.update_session_group(
            option.id, new_name
        )
        # update existing option in list
        self.session_groups[option.id] = updated_session_group
        option_list.replace_option_prompt(option.id, new_name)

    @work
    async def action_delete_session_group(self):
        option_list = self.query_exactly_one(OptionList)
        if not option_list.highlighted_option:
            return

        if (
            self.app.session_group
            == self.session_groups[option_list.highlighted_option.id]
        ):
            self.notify(
                "can't delete workspace as its current active workspace",
                severity="error",
            )
            return

        await self.app.db_manager.delete_session_group(
            option_list.highlighted_option.id
        )
        option_list.remove_option(option_list.highlighted_option.id)
