from textual import work

from dyno_viewer.components.screens.create_saved_query import CreateSavedQueryScreen
from dyno_viewer.db.models import SavedQuery


from textual.widgets import Input, Button, Static
from textual.app import App
from textual.reactive import reactive


async def test_create_saved_query_screen_submit_saved_query():
    class TestCreateSavedQueryScreen(App):
        BINDINGS = [("s", "create_saved_query", "Create Saved Query")]

        saved_query = reactive(None)

        @work
        async def action_create_saved_query(self):
            self.saved_query = await self.push_screen_wait(CreateSavedQueryScreen())

    async with TestCreateSavedQueryScreen().run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()

        screen = pilot.app.screen

        await pilot.pause()
        assert isinstance(screen, CreateSavedQueryScreen)

        query_name_input = screen.query_one("#query_name", Input)
        query_description_input = screen.query_one("#query_description", Input)
        create_button = screen.query_one("#create_button", Button)

        query_name_input.value = "Test Query"
        query_description_input.value = "This is a test saved query."

        create_button.action_press()

        await pilot.pause()

        assert isinstance(pilot.app.saved_query, SavedQuery)

        assert pilot.app.saved_query.name == "Test Query"
        assert pilot.app.saved_query.description == "This is a test saved query."


async def test_create_saved_query_screen_validation_click():
    class TestCreateSavedQueryScreen(App):
        BINDINGS = [("s", "create_saved_query", "Create Saved Query")]

        saved_query = reactive(None)

        @work
        async def action_create_saved_query(self):
            self.saved_query = await self.push_screen_wait(CreateSavedQueryScreen())

    async with TestCreateSavedQueryScreen().run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, CreateSavedQueryScreen)
        await pilot.click("#create_button")

        await pilot.pause()
        assert isinstance(pilot.app.screen, CreateSavedQueryScreen)

        error_message = pilot.app.screen.query_one("#name_error", Static)
        assert "cannot be empty" in error_message.content


async def test_create_saved_query_screen_validation_blur():
    class TestCreateSavedQueryScreen(App):
        BINDINGS = [("s", "create_saved_query", "Create Saved Query")]

        saved_query = reactive(None)

        @work
        async def action_create_saved_query(self):
            self.saved_query = await self.push_screen_wait(CreateSavedQueryScreen())

    async with TestCreateSavedQueryScreen().run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, CreateSavedQueryScreen)

        await pilot.press("tab")  # Focus on query name input
        await pilot.press("tab")  # Focus on query description input
        await pilot.press("enter")  # Try to create without a name

        await pilot.pause()
        assert isinstance(pilot.app.screen, CreateSavedQueryScreen)
        error_message = pilot.app.screen.query_one("#name_error", Static)
        assert "cannot be empty" in error_message.content
