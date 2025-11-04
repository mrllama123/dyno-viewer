from dyno_viewer.components.screens.help import HelpScreen
from textual.app import App


def test_help_screen(snap_compare):
    class TestApp(App):
        SCREENS = {
            "help": HelpScreen,
        }
        BINDINGS = [
            ("?", "show_help", "Show Help"),
        ]

        def action_show_help(self):
            self.push_screen("help")

    assert snap_compare(TestApp(), press=["?"], terminal_size=(100, 100))
