from dyno_viewer.components.screens.reaname_session_group import RenameSessionGroup
from dyno_viewer.components.screens.select_session_group import SelectSessionGroup
from textual.app import App
from textual.reactive import reactive
from textual import work
from textual.widgets import OptionList

from dyno_viewer.db.manager import DatabaseManager
from dyno_viewer.models import SessionGroup


async def test_select_session_group_first_row(db_manager: DatabaseManager):
    class TestApp(App):
        BINDINGS = [
            ("s", "select_workspace", "open select workspace screen"),
        ]
        db_manager = reactive(None)
        session_group = reactive(None)

        @work
        async def action_select_workspace(self):
            self.session_group = await self.push_screen_wait(SelectSessionGroup())

    session_groups = [
        SessionGroup(
            name=f"Test Workspace {i}",
        )
        for i in range(5)
    ]
    for session_group in session_groups:
        await db_manager.add_session_group(session_group)
    async with TestApp().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        workspace_option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert workspace_option_list.option_count == 5
        await pilot.press("tab", "down", "enter")
        await pilot.pause()
        assert pilot.app.session_group.session_group in session_groups


async def test_select_session_group_search(db_manager: DatabaseManager):
    class TestApp(App):
        BINDINGS = [
            ("s", "select_workspace", "open select workspace screen"),
        ]
        db_manager = reactive(None)
        session_group = reactive(None)

        @work
        async def action_select_workspace(self):
            self.session_group = await self.push_screen_wait(SelectSessionGroup())

    session_groups = [
        SessionGroup(name="test workspace 1"),
        SessionGroup(
            name="another test workspace",
        ),
        SessionGroup(
            name="yet another test workspace",
        ),
        SessionGroup(
            name="the last test workspace",
        ),
    ]
    for session_group in session_groups:
        await db_manager.add_session_group(session_group)

    async with TestApp().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        workspace_option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert workspace_option_list.option_count == 4
        await pilot.press("y", "e", "t", "enter")
        assert workspace_option_list.option_count == 1
        await pilot.press("tab", "down", "enter")
        await pilot.pause()
        assert pilot.app.session_group.session_group  == session_groups[2]


async def test_select_session_group_dismiss_before_choice(db_manager: DatabaseManager):
    class TestApp(App):
        BINDINGS = [
            ("s", "select_workspace", "open select workspace screen"),
        ]
        db_manager = reactive(None)
        session_group = reactive(None)

        @work
        async def action_select_workspace(self):
            self.session_group = await self.push_screen_wait(SelectSessionGroup())

    async with TestApp().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.press("escape")
        assert not isinstance(pilot.app.screen, SelectSessionGroup)
        assert not pilot.app.session_group


async def test_select_session_group_rename(db_manager: DatabaseManager):
    class TestApp(App):
        BINDINGS = [
            ("s", "select_workspace", "open select workspace screen"),
        ]
        db_manager = reactive(None)
        workspace = reactive(None)

        @work
        async def action_select_workspace(self):
            self.workspace = await self.push_screen_wait(SelectSessionGroup())

    session_groups = [
        SessionGroup(
            name=f"Test Workspace {i}",
        )
        for i in range(5)
    ]
    for session_group in session_groups:
        await db_manager.add_session_group(session_group)
    async with TestApp().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert option_list.option_count == 5
        await pilot.press("tab", "down", "r")
        await pilot.pause()
        assert isinstance(pilot.app.screen, RenameSessionGroup)
        await pilot.press("a", "b", "enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert "ab" in [option.prompt for option in option_list.options]
        list_session_group_result = await db_manager.list_session_group()
        assert "ab" in [row.data.name for row in list_session_group_result]


async def test_select_session_group_delete(db_manager: DatabaseManager):
    class TestApp(App):
        BINDINGS = [
            ("s", "select_workspace", "open select workspace screen"),
        ]
        db_manager = reactive(None)
        session_group = reactive(None)

        @work
        async def action_select_workspace(self):
            self.session_group = await self.push_screen_wait(SelectSessionGroup())

    session_groups = [
        SessionGroup(
            name=f"Test Workspace {i}",
        )
        for i in range(5)
    ]
    for session_group in session_groups:
        await db_manager.add_session_group(session_group)
    async with TestApp().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert option_list.option_count == 5
        await pilot.press("tab", "down", "d")
        await pilot.pause()
        option_list = pilot.app.screen.query_exactly_one(OptionList)
        assert "Test Workspace 0" not in [
            option.prompt for option in option_list.options
        ]
        list_session_group_result = await db_manager.list_session_group()
        assert "Test Workspace 0" not in [
            row.data.name for row in list_session_group_result
        ]
