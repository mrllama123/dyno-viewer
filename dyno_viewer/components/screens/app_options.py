from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown, OptionList
from textual.widgets.option_list import Option

from dyno_viewer.messages import ClearQueryHistory


class AppOptions(ModalScreen):
    BINDINGS = [("escape", "exit", "Close the modal")]
    DEFAULT_CSS = """
    
    #optionScreen {
        # layout: grid;
        # grid-size: 1;
        # overflow-y: auto;
        margin: 1 1;
        background: $boost;
        border: heavy grey;
        height: 26;
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
    #clearQueryHistoryButton {
        margin: 1 1;
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
        page_size_input.value = str(
            self.app.app_config.page_size if self.app.app_config.page_size else 20
        )
        for theme_name in self.app.available_themes:
            theme_option_list.add_option(Option(theme_name, id=theme_name))

    def action_exit(self) -> None:
        if self.app.app_config:
            theme_option_list = self.query_one("#themeOptionList", OptionList)
            selected_theme = theme_option_list.highlighted_option
            if selected_theme:
                self.app.app_config.theme = selected_theme.id
            page_size_input = self.query_one("#pageSizeInput", Input)
            if page_size_input.value.isdigit():
                self.app.app_config.page_size = int(page_size_input.value)
            self.app.app_config.save_config()
        self.app.pop_screen()
