from textwrap import dedent

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Markdown

from dyno_viewer.components.screens import (
    ProfileSelectScreen,
    QueryHistoryScreen,
    QueryScreen,
    RegionSelectScreen,
    SavedQueriesScreen,
    TableSelectScreen,
    TableViewer,
)

# constant here to not cause circular imports
SCREEN_CLASSES: list[Screen | ModalScreen] = [
    TableViewer,
    QueryScreen,
    ProfileSelectScreen,
    RegionSelectScreen,
    TableSelectScreen,
    QueryHistoryScreen,
    SavedQueriesScreen,
]


class HelpScreen(ModalScreen):
    DEFAULT_CSS = """
        HelpScreen {
            border: vkey $foreground 30%;
            layout: vertical;
            height: 100%;
        }
    """
    BINDINGS = [Binding("escape", "app.pop_screen")]

    def get_all_bindings(self) -> dict[str, tuple[list[Binding], str | None]]:
        return {
            "app": (
                [
                    *list(Binding.make_bindings(self.app.BINDINGS)),
                    Binding(
                        "escape", action="app.pop_screen", description="Exit popup"
                    ),  # add here as its used in all popup screens
                ],
                "## Global Commands",
            ),
            **{
                screen.__qualname__: (
                    [
                        binding
                        for binding in Binding.make_bindings(screen.BINDINGS)
                        # filter out pop screen binding as its added globally
                        if binding.action != "app.pop_screen"
                    ],
                    dedent(screen.HELP.strip()) if screen.HELP else None,
                )
                for screen in SCREEN_CLASSES
            },
        }

    def compose(self) -> ComposeResult:
        yield Markdown("# key mappings")

    def on_mount(self):
        all_bindings = self.get_all_bindings()

        for screen_name, (screen_bindings, screen_help) in all_bindings.items():
            if screen_bindings:
                table = DataTable(
                    id=f"{screen_name}-bindings", disabled=True, cursor_type="none"
                )
                table.add_columns("key", "action", "description")
                for binding in screen_bindings:
                    table.add_row(binding.key, binding.description, binding.tooltip)
                self.mount_all([Markdown(screen_help or f"## {screen_name}"), table])
