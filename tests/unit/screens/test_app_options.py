from textual import on, work
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Button, Input, OptionList

from dyno_viewer.components.screens.app_options import AppOptions
from dyno_viewer.db.models import RecordType
from dyno_viewer.models import KeyCondition, QueryParameters
from dyno_viewer.messages import ClearQueryHistory
from dyno_viewer.models import Config
from datetime import datetime
from zoneinfo import ZoneInfo
import time_machine


class OptionsTestApp(App):
    SCREENS = {
        "options": AppOptions,
    }

    BINDINGS = [
        ("o", "show_options", "Show Options"),
    ]
    app_config = reactive(None)
    db_manager = reactive(None)

    @work(exclusive=True, group="purge_query_history")
    async def worker_delete_query_history(self) -> None:
        """Clear all query history from the database."""
        if not self.db_manager:
            return
        await self.db_manager.remove_all_query_history()
        self.notify("Query history cleared.")

    @on(ClearQueryHistory)
    async def process_clear_query_history_request(self, _: ClearQueryHistory) -> None:
        self.worker_delete_query_history()

    def watch_theme(self, new_theme: str) -> None:
        self.app_config.theme = new_theme
        self.app_config.save_config()

    def action_show_options(self):
        self.push_screen("options")


async def test_initial_options_display(user_config_dir_tmp_path):
    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        config_path = user_config_dir_tmp_path / "config.yaml"
        assert config_path.exists()
        assert (
            config_path.read_text()
            == "load_last_query_on_startup: true\npage_size: 20\ntheme: textual-dark\n"
        )
        await pilot.press("o")

        screen = pilot.app.screen
        assert isinstance(screen, AppOptions)
        option_list = screen.query_one(OptionList)
        page_input = screen.query_one(Input)

        option_ids = [option.id for option in option_list.options]
        for theme in pilot.app.available_themes:
            assert theme in option_ids, f"Theme '{theme}' should be in options"

        page_input.value == str(20)


async def test_theme_selection_updates_app_theme(user_config_dir_tmp_path):
    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        await pilot.press("o")

        screen = pilot.app.screen
        option_list = screen.query_one(OptionList)

        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("enter")

        assert pilot.app.theme == option_list.highlighted_option.id
        await pilot.pause()

        config_path = user_config_dir_tmp_path / "config.yaml"
        assert (
            config_path.read_text()
            == f"load_last_query_on_startup: true\npage_size: 20\ntheme: {option_list.highlighted_option.id}\n"
        )


async def test_exit_saves_theme_and_page_size(user_config_dir_tmp_path):
    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        await pilot.press("o")
        screen = pilot.app.screen
        option_list = screen.query_one(OptionList)
        page_input = screen.query_one(Input)

        # Select a specific theme (e.g., second one)
        await pilot.press("down")
        await pilot.press("enter")
        # Set page size
        page_input.focus()
        await pilot.press("5", "5")

        # Exit (escape binding triggers action_exit)
        await pilot.press("escape")

        # Screen should be popped
        assert not isinstance(pilot.app.screen, AppOptions)

        # Config should reflect selections and be saved
        assert pilot.app.app_config.theme == option_list.highlighted_option.id
        assert pilot.app.app_config.page_size == 55
        config_path = user_config_dir_tmp_path / "config.yaml"
        assert (
            config_path.read_text()
            == f"load_last_query_on_startup: true\npage_size: 55\ntheme: {option_list.highlighted_option.id}\n"
        )


async def test_load_last_query_switch(user_config_dir_tmp_path):
    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        await pilot.press("o")
        screen = pilot.app.screen
        load_last_query_switch = screen.query_one("#loadLastQuerySwitch")

        # Toggle the switch
        load_last_query_switch.toggle()

        # Exit to save config
        await pilot.press("escape")

        # Config should reflect the switch state
        assert pilot.app.app_config.load_last_query_on_startup == False
        config_path = user_config_dir_tmp_path / "config.yaml"
        assert (
            config_path.read_text()
            == "load_last_query_on_startup: false\npage_size: 20\ntheme: textual-dark\n"
        )


async def test_clear_query_history(db_manager, user_config_dir_tmp_path):
    # Build three sample QueryHistory rows
    query_params = [
        QueryParameters(
            scan_mode=False,
            primary_key_name="pk",
            sort_key_name="sk",
            index="table",
            key_condition=KeyCondition(partitionKeyValue="A"),
            filter_conditions=[],
        ),
        QueryParameters(
            scan_mode=False,
            primary_key_name="pk",
            sort_key_name="sk",
            index="table",
            key_condition=KeyCondition(partitionKeyValue="B"),
            filter_conditions=[],
        ),
    ]
    for i, query_history in enumerate(query_params):
        with time_machine.travel(
            datetime(2024, 1, 1, 12, 0, i, tzinfo=ZoneInfo("UTC")), tick=False
        ):
            await db_manager.add_query_history(query_history)

    # Verify all query histories are in the DB
    list_query_history_result = await db_manager.list_query_history()
    for param in query_params:
        assert param in [row.data for row in list_query_history_result]
    async with db_manager.connection.execute(
        "SELECT COUNT(*) FROM data_store WHERE record_type = ?",
        (RecordType.QueryHistory.value,),
    ) as cursor:
        row = await cursor.fetchone()
        assert len(row) == 1
        assert row[0] == 2

    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        pilot.app.db_manager = db_manager
        await pilot.press("o")
        screen = pilot.app.screen

        button = screen.query_one(Button)
        # Simulate button press
        button.press()
        await pilot.pause(0.5)

        # Verify that query history is cleared
        list_query_history_result = await db_manager.list_query_history()
        for query_history in query_params:
            assert query_history not in [row.data for row in list_query_history_result]
        async with db_manager.connection.execute(
            "SELECT COUNT(*) FROM data_store WHERE record_type = ?",
            (RecordType.QueryHistory.value,),
        ) as cursor:
            row = await cursor.fetchone()
            assert len(row) == 1
            assert row[0] == 0
