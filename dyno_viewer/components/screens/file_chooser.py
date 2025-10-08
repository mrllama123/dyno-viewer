from pathlib import Path

from textual import on
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label, Markdown, OptionList
from textual.widgets.option_list import Option

from dyno_viewer.models import FileToSave, OutputFormat


class SaveFileChooser(ModalScreen):

    DEFAULT_CSS = """
    * {
        overflow-y: auto;
    }
    #title {
        text-align: center;
        height: 3;
    }
    #filename {
        height: 5;
        layout: vertical;
        text-align: center;
    }
    #buttons {
        height: 5;
        layout: horizontal;
        align-horizontal: center;
        padding: 1 2;
        dock: bottom;
    }
    #filetree {
        layout: horizontal;
    }
    #navbar {
        height: 100%;
        width: 18;
        layout: vertical;
     
    }

    """

    path_selected = reactive(Path.home())
    base_directory = reactive(Path.home(), init=False)
    file_format: OutputFormat = reactive(OutputFormat.CSV)

    def __init__(self, default_filename: str = "") -> None:
        super().__init__()
        self.title = "Save a file"
        self.default_filename = default_filename

    def compose(self):
        yield Markdown(f"# {self.title}", id="title")

        with Container(id="filename"):
            yield Label(" File name:", id="filename_label")
            yield (
                Input(value=self.default_filename, id="filename_input")
                if self.default_filename
                else Input(id="filename_input")
            )
        with Container(id="filetree"):
            with Container(id="navbar"):
                yield Label("Quick Navigation:")
                yield OptionList(
                    Option("home", id="home"), Option("root", id="root"), id="quicknav"
                )
                yield Label("File format:")
                yield OptionList(
                    *[Option(format.value, id=format) for format in OutputFormat],
                    id="fileformat",
                )
            yield DirectoryTree(self.base_directory)
        with Container(id="buttons"):
            yield Button("Ok", id="ok")
            yield Button("Cancel", id="cancel")

    @on(DirectoryTree.DirectorySelected)
    def directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.path_selected = event.path

    @on(OptionList.OptionSelected, "#quicknav")
    def quicknav_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "home":
            self.base_directory = Path.home()
        elif event.option.id == "root":
            self.base_directory = Path("/")

    @on(OptionList.OptionSelected, "#fileformat")
    def fileformat_selected(self, event: OptionList.OptionSelected) -> None:
        self.file_format = event.option.id

    @on(Button.Pressed, "#ok")
    async def ok_pressed(self, _: Button.Pressed) -> None:
        filename = self.query_one("#filename_input").value
        if not filename:
            self.app.notify("Please enter a file name", severity="warning")
            return
        path = self.path_selected / filename

        self.dismiss(FileToSave(path=path, file_format=self.file_format))

    @on(Button.Pressed, "#cancel")
    async def cancel_pressed(self, _: Button.Pressed) -> None:
        self.dismiss(None)

    def watch_base_directory(self, new_path: Path) -> None:
        query_directory_tree = self.query(DirectoryTree)
        if not query_directory_tree:
            return

        if new_path:
            directory_tree = query_directory_tree[0]
            if directory_tree.path == new_path:
                return
            directory_tree.path = new_path
            directory_tree.refresh()
