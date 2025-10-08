# python
from pathlib import Path

from textual.app import App
from textual.pilot import Pilot
from textual.widgets import Button, OptionList, DirectoryTree

from dyno_viewer.components.screens.file_chooser import SaveFileChooser
from dyno_viewer.models import OutputFormat, FileToSave


class TestHostApp(App):

    def __init__(self, screen: SaveFileChooser):
        super().__init__()
        self._screen = screen
        self.notifications = []
        self.dismissed_result = None

    def notify(self, message, severity="info"):
        # Capture notifications rather than display
        self.notifications.append((message, severity))

    async def on_mount(self):
        def _callback(result):
            self.dismissed_result = result

        self.push_screen(self._screen, _callback)


async def select_option_in_option_list(
    pilot: Pilot, option_list: OptionList, index: int
):
    pilot.app.set_focus(option_list)
    await pilot.pause()
    # Move to first (ensure deterministic)
    # Send several "home" just in case
    await pilot.press("home")
    await pilot.pause()
    for _ in range(index):
        await pilot.press("down")
        await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def test_ok_without_filename_shows_notification():
    screen = SaveFileChooser()
    async with TestHostApp(screen).run_test() as pilot:
        ok_button = screen.query_one("#ok", Button)
        ok_button.press()
        await pilot.pause()
        assert pilot.app.notifications, "Expected a notification when filename missing"
        message, severity = pilot.app.notifications[-1]
        assert "Please enter a file name" in message
        assert severity == "warning"
        # Screen should not have dismissed
        assert pilot.app.dismissed_result is None


async def test_ok_with_filename_returns_file_to_save():
    filename = "test_export.csv"
    screen = SaveFileChooser(default_filename=filename)
    async with TestHostApp(screen).run_test() as pilot:
        ok_button = screen.query_one("#ok", Button)
        ok_button.press()
        await pilot.pause()
        result = pilot.app.dismissed_result
        assert isinstance(result, FileToSave)
        assert result.path == screen.path_selected / filename
        assert result.file_format == OutputFormat.CSV


async def test_quicknav_root_changes_directory_tree():
    screen = SaveFileChooser(default_filename="file.txt")
    async with TestHostApp(screen).run_test() as pilot:
        quicknav = screen.query_one("#quicknav", OptionList)
        # Options order: home (index 0), root (index 1)
        await select_option_in_option_list(pilot, quicknav, 1)
        assert screen.base_directory == Path("/")
        dir_tree = screen.query(DirectoryTree)[0]
        assert dir_tree.path == Path("/")


async def test_file_format_selection_json_updates_reactive_and_return_value():
    screen = SaveFileChooser(default_filename="datafile")
    async with TestHostApp(screen).run_test() as pilot:
        file_format_list = screen.query_one("#fileformat", OptionList)
        await select_option_in_option_list(pilot, file_format_list, 1)

        ok_button = screen.query_one("#ok", Button)
        ok_button.press()
        await pilot.pause()
        result = pilot.app.dismissed_result
        assert isinstance(result, FileToSave)
        assert result.file_format == OutputFormat.JSON


async def test_watch_base_directory_no_duplicate_refresh():
    screen = SaveFileChooser(default_filename="noop.txt")
    async with TestHostApp(screen).run_test() as pilot:
        dir_tree = screen.query(DirectoryTree)[0]
        original_path_obj = dir_tree.path
        # Select "home" (index 0). Since already home, watcher should early return without changing path.
        quicknav = screen.query_one("#quicknav", OptionList)
        await select_option_in_option_list(pilot, quicknav, 0)
        # Path should remain identical object or at least equal; we check equality and that not changed to something else.
        assert dir_tree.path == original_path_obj
