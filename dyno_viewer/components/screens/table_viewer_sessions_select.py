from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Markdown, OptionList

from dyno_viewer.components.screens.create_rename_session import (
    RenameCreateSessionModal,
)


class TableViewerSessionsSelect(ModalScreen):
    """Modal screen for selecting sessions in the table viewer."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close the modal"),
        Binding("r", "rename_session", "Rename session", show=False),
    ]
    HELP = """
    ## Select Table Viewer Session
    """

    def compose(self) -> ComposeResult:
        yield Markdown("# Select Table Viewer Session")
        yield OptionList()

    def on_mount(self) -> None:
        option_list = self.query_one(OptionList)
        option_list.focus()
        self.update_sessions()

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_option = event.option
        self.dismiss(selected_option.prompt)

    def watch_sessions(self, sessions: list) -> None:
        """Watch for changes in the sessions reactive variable."""
        self.log(f"Sessions updated: {sessions}")
        if sessions:
            option_list = self.query_one(OptionList)
            option_list.clear_options()
            for session in sessions:
                option_list.add_option(session)
            option_list.action_first()

    @work
    async def action_rename_session(self) -> None:
        """Action to rename the selected session."""

        option_list = self.query_one(OptionList)
        selected_option = option_list.highlighted_option

        if selected_option:
            new_session_name = await self.app.push_screen_wait(
                RenameCreateSessionModal("Rename Table Viewer Session")
            )
            if new_session_name:
                self.app._installed_screens[new_session_name] = (
                    self.app._installed_screens.pop(selected_option.prompt)
                )
                self.update_sessions(select_session=new_session_name)

    def update_sessions(self, select_session: str | None = None) -> None:
        """Update the sessions list."""
        sessions = sorted(
            [
                screen_name
                for screen_name in self.app._installed_screens.keys()
                if self.app._installed_screens[screen_name].id.startswith("table_")
            ]
        )
        if sessions:
            option_list = self.query_one(OptionList)
            option_list.clear_options()
            for session in sessions:
                option_list.add_option(session)
            try:
                index = sessions.index(select_session)
                option_list.highlighted = index
            except ValueError:
                option_list.action_first()
            except Exception:
                raise
