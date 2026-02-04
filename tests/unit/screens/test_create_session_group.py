from textual.app import App
from textual import work

from textual.reactive import reactive

from dyno_viewer.components.screens.create_session_group import CreateSessionGroup


async def test_create_workspace_return_name():
    class TestApp(App):
        BINDINGS = [
            ("w", "create_workspace", "Create new workspace"),
        ]
        session_group_name = reactive(None)

        @work
        async def action_create_workspace(self):
            self.session_group_name = await self.push_screen_wait(CreateSessionGroup())

    async with TestApp().run_test() as pilot:
        await pilot.press("w")
        assert isinstance(pilot.app.screen, CreateSessionGroup)
        await pilot.press("tab", "t", "e", "s", "t", "enter")
        await pilot.pause()
        assert not isinstance(pilot.app.screen, CreateSessionGroup)
        assert pilot.app.session_group_name == ("test", False)


async def test_create_workspace_pop_screen():
    class TestApp(App):
        BINDINGS = [
            ("w", "create_workspace", "Create new workspace"),
        ]
        session_group_name = reactive(None)

        @work
        async def action_create_workspace(self):
            self.session_group_name = await self.push_screen_wait(CreateSessionGroup())

    async with TestApp().run_test() as pilot:
        await pilot.press("w")
        assert isinstance(pilot.app.screen, CreateSessionGroup)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(pilot.app.screen, CreateSessionGroup)
        assert not pilot.app.session_group_name
