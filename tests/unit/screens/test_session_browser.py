from dyno_viewer.components.screens.create_rename_session import RenameCreateSession
from dyno_viewer.db.manager import DatabaseManager
from dyno_viewer.components.screens import SessionBrowser, SelectSessionGroup
from dyno_viewer.app import DynCli
from textual.reactive import reactive
from textual import work
from textual.app import App
from textual.widgets import OptionList, Input, DataTable
from dyno_viewer.models import SessionGroup, Session


async def test_session_browser_no_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):

    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("j")
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 1
        first_row = table.get_row_at(0)
        assert first_row == ["default_table", None, "ap-southeast-2", ""]


async def test_session_browser_no_session_add_new_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):

    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("j")
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 1
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]
        await pilot.press("a")
        assert isinstance(pilot.app.screen, RenameCreateSession)
        await pilot.press("t", "e", "s", "t", "1", "enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        assert table.row_count == 2
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]
        assert table.get_row_at(1) == ["test1", None, "ap-southeast-2", ""]


async def test_session_browser_no_session_remove_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):

    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("j")
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 1
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]
        await pilot.press("a")
        assert isinstance(pilot.app.screen, RenameCreateSession)
        await pilot.press("t", "e", "s", "t", "1", "enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        assert table.row_count == 2
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]
        assert table.get_row_at(1) == ["test1", None, "ap-southeast-2", ""]
        await pilot.press("tab", "tab", "down", "down", "d")
        assert table.row_count == 1
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]


async def test_session_browser_no_session_rename_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):

    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("j")
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 1
        assert table.get_row_at(0) == ["default_table", None, "ap-southeast-2", ""]
        await pilot.press("tab", "tab", "r")
        assert isinstance(pilot.app.screen, RenameCreateSession)
        await pilot.press("t", "e", "s", "t", "1", "enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        assert table.row_count == 1
        assert table.get_row_at(0) == ["test1", None, "ap-southeast-2", ""]


async def test_session_browser_with_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):
    session_group = SessionGroup(
        name="test_session_group",
    )
    sessions = [
        Session(
            name="test_session 1",
            aws_profile="profile_1",
            aws_region="ap-southeast-2",
            table_name="",
            session_group_id=session_group.session_group_id,
        ),
        Session(
            name="test_session 2",
            aws_profile="profile_2",
            aws_region="ap-northeast-1",
            table_name="",
            session_group_id=session_group.session_group_id,
        ),
    ]

    await db_manager.add_session_group(session_group)
    await db_manager.add_sessions(sessions)
    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("v")
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.press("tab", "down", "enter")
        assert not isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.pause()
        pilot.app.session_group == session_group
        await pilot.press("j")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 2
        assert table.get_row_at(0) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        assert table.get_row_at(1) == [
            "test_session 2",
            "profile_2",
            "ap-northeast-1",
            "",
        ]


async def test_session_browser_with_session_add_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):
    session_group = SessionGroup(
        name="test_session_group",
    )
    sessions = [
        Session(
            name="test_session 1",
            aws_profile="profile_1",
            aws_region="ap-southeast-2",
            table_name="",
            session_group_id=session_group.session_group_id,
        ),
    ]

    await db_manager.add_session_group(session_group)
    await db_manager.add_sessions(sessions)
    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("v")
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.press("tab", "down", "enter")
        assert not isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.pause()
        pilot.app.session_group == session_group
        await pilot.press("j")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        table.row_count == 1
        assert table.get_row_at(0) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(pilot.app.screen, RenameCreateSession)
        await pilot.press("t", "e", "s", "t", "1", "enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        assert table.row_count == 2
        assert table.get_row_at(0) == ["test1", None, "ap-southeast-2", ""]
        assert table.get_row_at(1) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        


async def test_session_browser_with_session_remove_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):
    session_group = SessionGroup(
        name="test_session_group",
    )
    sessions = [
        Session(
            name="test_session 1",
            aws_profile="profile_1",
            aws_region="ap-southeast-2",
            table_name="",
            session_group_id=session_group.session_group_id,
        ),
        Session(
            name="test_session 2",
            aws_profile="profile_2",
            aws_region="ap-northeast-1",
            table_name="",
            session_group_id=session_group.session_group_id,
        ),
    ]

    await db_manager.add_session_group(session_group)
    await db_manager.add_sessions(sessions)
    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("v")
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.press("tab", "down", "enter")
        assert not isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.pause()
        pilot.app.session_group == session_group
        await pilot.press("j")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        assert table.row_count == 2
        assert table.get_row_at(0) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        assert table.get_row_at(1) == [
            "test_session 2",
            "profile_2",
            "ap-northeast-1",
            "",
        ]
        await pilot.press("tab", "tab", "down", "down", "d")
        assert table.row_count == 1
        assert table.get_row_at(0) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        assert sessions[1] not in [
            session.data for session in await db_manager.list_sessions()
        ]


async def test_session_browser_with_session_rename_session(
    db_manager: DatabaseManager, ddb_table_with_data, ddb_tables
):
    session_group = SessionGroup(
        name="test_session_group",
    )
    session = Session(
        name="test_session 1",
        aws_profile="profile_1",
        aws_region="ap-southeast-2",
        table_name="",
        session_group_id=session_group.session_group_id,
    )

    await db_manager.add_session_group(session_group)
    await db_manager.add_session(session)
    async with DynCli().run_test() as pilot:
        pilot.app.db_manager = db_manager
        await pilot.press("v")
        assert isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.press("tab", "down", "enter")
        assert not isinstance(pilot.app.screen, SelectSessionGroup)
        await pilot.pause()
        pilot.app.session_group == session_group
        await pilot.press("j")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionBrowser)
        table = pilot.app.screen.query_exactly_one(DataTable)
        table.row_count == 1
        assert table.get_row_at(0) == [
            "test_session 1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        await pilot.press("tab", "tab", "down", "r")
        await pilot.pause()
        assert isinstance(pilot.app.screen, RenameCreateSession)
        await pilot.press("t", "e", "s", "t", "1", "enter")
        assert isinstance(pilot.app.screen, SessionBrowser)
        table.row_count == 1
        assert table.get_row_at(0) == [
            "test1",
            "profile_1",
            "ap-southeast-2",
            "",
        ]
        updated_session = await db_manager.get_session(session.session_id)
        assert updated_session.name == "test1"
