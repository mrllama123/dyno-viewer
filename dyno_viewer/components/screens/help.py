import os

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Markdown


class HelpMenu(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with open(
            os.path.join(parent_dir, "help", "help-doc.md"), encoding="utf-8"
        ) as f:
            text = f.read()
            yield Markdown(text, id="helpMarkdown")
