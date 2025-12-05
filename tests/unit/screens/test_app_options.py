from textual import on, work
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Button, Input, OptionList

from dyno_viewer.components.screens.app_options import AppOptions
from dyno_viewer.db.models import QueryHistory, KeyCondition
from dyno_viewer.messages import ClearQueryHistory
from dyno_viewer.models import Config
from dyno_viewer.db.utils import delete_all_query_history
from datetime import datetime


class OptionsTestApp(App):
    SCREENS = {
        "options": AppOptions,
    }

    BINDINGS = [
        ("o", "show_options", "Show Options"),
    ]
    app_config = reactive(None)
    db_session = reactive(None)

    @work(exclusive=True, group="purge_query_history")
    async def worker_delete_query_history(self) -> None:
        """Clear all query history from the database."""
        if not self.db_session:
            return
        await delete_all_query_history(self.db_session)
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
        assert config_path.read_text() == "page_size: 20\ntheme: textual-dark\n"
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
            == f"page_size: 20\ntheme: {option_list.highlighted_option.id}\n"
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
            == f"page_size: 55\ntheme: {option_list.highlighted_option.id}\n"
        )


async def test_clear_query_history(db_session, user_config_dir_tmp_path):
    # Build three sample QueryHistory rows
    async with db_session.begin():

        # created_at descending should show row3 first
        db_session.add_all(
            [
                QueryHistory(
                    scan_mode=False,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=KeyCondition(partitionKeyValue="A").model_dump_json(),
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
                QueryHistory(
                    scan_mode=True,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=None,
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, 1),
                ),
                QueryHistory(
                    scan_mode=False,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=KeyCondition(partitionKeyValue="B").model_dump_json(),
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, 2),
                ),
            ]
        )

    await db_session.commit()
    async with OptionsTestApp().run_test() as pilot:
        pilot.app.app_config = Config.load_config()
        pilot.app.db_session = db_session
        await pilot.press("o")
        screen = pilot.app.screen

        button = screen.query_one(Button)
        # Simulate button press
        button.press()
        await pilot.pause(0.5)

        # Verify that query history is cleared
        result = await db_session.execute(QueryHistory.__table__.select())
        rows = result.fetchall()
        assert len(rows) == 0

