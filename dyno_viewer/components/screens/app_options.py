from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown, OptionList, Switch
from textual.widgets.option_list import Option

from dyno_viewer.messages import ClearQueryHistory


class AppOptions(ModalScreen):
    BINDINGS = [("escape", "exit", "Close the modal")]
    DEFAULT_CSS = """
    
    #optionScreen {
        margin: 1 1;
        background: $boost;
        border: heavy grey;
        height: 38;
    }
    #themeContainer OptionList {
        height: 8;
    }
    #themeContainer {
        height: 10;
        margin-bottom: 1;
    }

    #pageSizeContainer  {
        height: 5;
    }
    #loadLastQueryContainer  {
        height: 5;
    }
    #clearQueryHistoryButton {
        margin: 1 1;
    }#SessionGroupContainer  {
        height: 5;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="optionScreen"):
            yield Markdown("# Application Options")
            with Container(id="themeContainer"):
                yield Label("Themes:")
                yield OptionList(id="themeOptionList")
            with Container(id="pageSizeContainer"):
                yield Label("Page Size:")
                yield Input(id="pageSizeInput")
            with Container(id="loadLastQueryContainer"):
                yield Label("Load Last Query on Startup:")
                yield Switch(
                    id="loadLastQuerySwitch",
                    value=self.app.app_config.load_last_query_on_startup,
                )
            with Container(id="SessionGroupContainer"):
                yield Label("Session group to load on startup:")
                yield Input(id="sessionGroupInput")
            yield Button(
                "Clear Query History", id="clearQueryHistoryButton", variant="error"
            )

    @on(OptionList.OptionSelected, "#themeOptionList")
    def theme_selected(self, event: OptionList.OptionSelected) -> None:
        if selected_option := event.option:
            self.app.theme = selected_option.id

    @on(Button.Pressed, "#clearQueryHistoryButton")
    async def clear_query_history_pressed(self, _: Button.Pressed) -> None:
        self.post_message(ClearQueryHistory())

    def on_mount(self) -> None:
        theme_option_list = self.query_one("#themeOptionList", OptionList)
        page_size_input = self.query_one("#pageSizeInput", Input)
        session_group_input = self.query_one("#sessionGroupInput", Input)
        page_size_input.value = str(
            self.app.app_config.page_size if self.app.app_config.page_size else 20
        )
        if self.app.app_config.startup_session_group:
            session_group_input.value = self.app.app_config.startup_session_group
        for theme_name in self.app.available_themes:
            theme_option_list.add_option(Option(theme_name, id=theme_name))

    async def action_exit(self) -> None:

        theme_option_list = self.query_one("#themeOptionList", OptionList)
        load_last_query_switch = self.query_one("#loadLastQuerySwitch", Switch)
        page_size_input = self.query_one("#pageSizeInput", Input)
        session_group_input = self.query_one("#sessionGroupInput", Input)
        if selected_theme := theme_option_list.highlighted_option:
            self.app.app_config.theme = selected_theme.id
        if page_size_input.value.isdigit():
            self.app.app_config.page_size = int(page_size_input.value)
        self.app.app_config.load_last_query_on_startup = load_last_query_switch.value
        if (
            session_group_input.value
            and not await self.app.db_manager.get_session_group_by_name(
                session_group_input.value
            )
        ):
            self.notify(
                "cannot find session group, Please try again", severity="warning"
            )
            return
        self.app.app_config.startup_session_group = session_group_input.value
        self.app.app_config.save_config()
        self.app.pop_screen()
