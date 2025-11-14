import uuid
from textual.app import App
from textual.screen import Screen
from textual import work
from textual.widgets import OptionList, Static

from dyno_viewer.components.screens.table_viewer_sessions_select import (
    TableViewerSessionsSelect,
)
from dyno_viewer.components.screens.create_rename_session import (
    RenameCreateSessionModal,
)


class DummyTableScreen(Screen):
    def __init__(
        self, message: str, id: str | None = None
    ):  # noqa: A003 textual uses id param
        super().__init__(id=id)
        self.message = message

    def compose(self):
        yield Static(self.message)


async def test_select_session():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        # first option should be a_session because list sorted
        option_list = screen.query_one(OptionList)
        # textual OptionList children hold options; ensure sorted order
        prompts = [c.prompt for c in option_list.children]
        assert prompts == sorted(prompts)
        # select highlighted (first) session
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DummyTableScreen)
        assert pilot.app.screen.message == "table_beta"


async def test_select_multiple_sessions():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        # First selection
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DummyTableScreen)
        assert pilot.app.screen.message == "table_beta"
        # Second selection
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        # move to next option
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DummyTableScreen)
        assert pilot.app.screen.message == "table_alpha"


async def test_cancel_selection():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        # cancel selection
        await pilot.press("escape")
        await pilot.pause()
        # should still be on default table screen
        assert isinstance(pilot.app.screen, DummyTableScreen)
        assert pilot.app.screen.message == "table_default"


async def test_rename_session():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        await pilot.pause()
        # rename currently highlighted (a_session)
        await pilot.press("r")
        rename_screen = pilot.app.screen
        assert isinstance(rename_screen, RenameCreateSessionModal)
        # type new name and submit
        await pilot.press(*list("renamed_session"))
        await pilot.press("enter")
        # allow async work to finish
        await pilot.pause()
        # Back on selection screen
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        # confirm installed screens updated
        assert "renamed_session" in pilot.app._installed_screens
        assert "a_session" not in pilot.app._installed_screens
        # allow session list to refresh
        await pilot.pause()
        option_list = screen.query_one(OptionList)
        prompts = [c.prompt for c in option_list.options]
        assert "renamed_session" in prompts
        # highlighted option should be renamed_session
        assert option_list.highlighted_option.prompt == "renamed_session"


async def test_rename_multiple_sessions():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        # First rename
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        await pilot.pause()
        await pilot.press("r")
        rename_screen = pilot.app.screen
        assert isinstance(rename_screen, RenameCreateSessionModal)
        await pilot.press(*list("first_rename"))
        await pilot.press("enter")
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        assert "first_rename" in pilot.app._installed_screens
        # Second rename
        await pilot.press("r")
        rename_screen = pilot.app.screen
        assert isinstance(rename_screen, RenameCreateSessionModal)
        await pilot.press(*list("second_rename"))
        await pilot.press("enter")
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        assert "second_rename" in pilot.app._installed_screens
        assert "first_rename" not in pilot.app._installed_screens


async def test_rename_cancel_selection():
    class SessionsApp(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        def on_mount(self) -> None:  # install some table screens in unsorted order
            self.install_screen(
                DummyTableScreen("table_default", id=f"table_{uuid.uuid4()}"),
                name="default_table",
            )
            self.install_screen(
                DummyTableScreen("table_alpha", id=f"table_{uuid.uuid4()}"),
                name="b_session",
            )
            self.install_screen(
                DummyTableScreen("table_beta", id=f"table_{uuid.uuid4()}"),
                name="a_session",
            )
            self.push_screen("default_table")

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsApp().run_test() as pilot:
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        await pilot.pause()
        # initiate rename
        await pilot.press("r")
        rename_screen = pilot.app.screen
        assert isinstance(rename_screen, RenameCreateSessionModal)
        # cancel rename
        await pilot.press("escape")
        await pilot.pause()
        # back on selection screen
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        # installed screens should be unchanged
        assert "a_session" in pilot.app._installed_screens
        # highlighted option should still be a_session
        option_list = screen.query_one(OptionList)
        assert option_list.highlighted_option.prompt == "a_session"


async def test_no_sessions():
    class SessionsAppNoTables(App):
        BINDINGS = [
            ("v", "select_session", "Select Table Viewer Session"),
        ]

        @work
        async def action_select_session(self):
            screen_name = await self.push_screen_wait(TableViewerSessionsSelect())
            if screen_name:
                await self.push_screen(screen_name)

    async with SessionsAppNoTables().run_test() as pilot:
        await pilot.press("v")
        screen = pilot.app.screen
        assert isinstance(screen, TableViewerSessionsSelect)
        option_list = screen.query_one(OptionList)
        assert len(option_list.options) == 0
