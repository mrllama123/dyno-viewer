import asyncio
from datetime import datetime


from textual.app import App
from textual.widgets import DataTable

from dyno_viewer.components.screens.confirm_dialogue import ConfirmDialogue
from dyno_viewer.components.screens.query_history_browser import QueryHistoryBrowser
from dyno_viewer.db.models import RecordType
from dyno_viewer.db.queries import add_query_history, list_query_history
from dyno_viewer.constants import FILTER_CONDITIONS, ATTRIBUTE_TYPES
from dyno_viewer.models import KeyCondition, QueryParameters, FilterCondition
import time_machine


async def test_query_history_screen_populates_from_db(data_store_db_session):
    """Ensure the screen reads query history rows from the DB and displays them."""

    # Build three sample QueryHistory rows
    # async with db_session.begin():
    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 0), tick=False):
        await add_query_history(
            data_store_db_session,
            QueryParameters(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="A"),
                filter_conditions=[],
            ),
        )
    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 2), tick=False):
        await add_query_history(
            data_store_db_session,
            QueryParameters(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="B"),
                filter_conditions=[],
            ),
        )

    class TestApp(App):
        CSS = ""

        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(data_store_db_session).run_test() as pilot:
        # allow background worker to complete
        await pilot.pause(0.05)
        screen = pilot.app.screen
        assert isinstance(screen, QueryHistoryBrowser)
        table = screen.query_one(DataTable)
        assert table.row_count == 2
        # Ensure ordering is newest first (created_at descending)
        first_row = table.get_row_at(0)
        last_row = table.get_row_at(1)
        assert first_row == ["2024-01-01 12:00:02+00:00", False, "pk = 'B'", ""]
        assert last_row == ["2024-01-01 12:00:00+00:00", False, "pk = 'A'", ""]


async def test_query_history_screen_with_filters(data_store_db_session):
    """Ensure the screen reads query history rows with filter conditions from the DB and displays them."""

    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 0), tick=False):
        await add_query_history(
            data_store_db_session,
            QueryParameters(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="A"),
                filter_conditions=[
                    FilterCondition(
                        attrValue="active",
                        attrCondition=FILTER_CONDITIONS[0],
                        attrName="status",
                        attrType=ATTRIBUTE_TYPES[0],
                    )
                ],
            ),
        )

    class TestApp(App):
        CSS = ""

        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(data_store_db_session).run_test() as pilot:
        # allow background worker to complete
        await pilot.pause(0.05)
        screen = pilot.app.screen
        assert isinstance(screen, QueryHistoryBrowser)
        table = screen.query_one(DataTable)
        assert table.row_count == 1
        first_row = table.get_row_at(0)
        assert first_row == [
            "2024-01-01 12:00:00+00:00",
            False,
            "pk = 'A'",
            "status = 'active'",
        ]


async def test_query_history_screen_pagination(data_store_db_session):
    """Verify pagination increments next_page until total_pages is reached."""

    for i in range(40):
        with time_machine.travel(datetime(2024, 1, 1, 12, 0, i % 60), tick=False):
            await add_query_history(
                data_store_db_session,
                QueryParameters(
                    scan_mode=False,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=KeyCondition(partitionKeyValue=str(i)),
                    filter_conditions=[],
                ),
            )

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(data_store_db_session).run_test() as pilot:
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        await pilot.pause()
        table = screen.query_one(DataTable)
        # After initial load only first 20 rows should be present
        assert table.row_count == 20
        assert screen.next_page == 2

        # Trigger next page via action
        await pilot.press("n")
        await pilot.pause()
        assert table.row_count == 40
        assert screen.next_page == 3

        await pilot.press("n")
        await pilot.pause()
        # No more rows should be added
        assert table.row_count == 40
        assert screen.next_page == 3


async def test_query_history_screen_row_selection(data_store_db_session):
    """Verify selecting a row returns the correct QueryParameters."""

    query_params = QueryParameters(
        scan_mode=False,
        primary_key_name="pk",
        sort_key_name="sk",
        index="table",
        key_condition=KeyCondition(partitionKeyValue="A"),
        filter_conditions=[],
    )

    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 0), tick=False):
        await add_query_history(data_store_db_session, query_params)

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session
            self.params = None

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    async with TestApp(data_store_db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 1

        # Select the first (and only) row
        await pilot.press("enter")
        await asyncio.sleep(0.05)

        # The screen should have been dismissed and returned QueryParameters

        assert pilot.app.params == query_params


async def test_query_history_screen_delete_row(data_store_db_session):
    """Verify deleting a row removes it from the screen and DB."""

    # Insert a sample QueryHistory row
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
            primary_key_name="pk2",
            sort_key_name="sk2",
            index="table2",
            key_condition=KeyCondition(partitionKeyValue="B"),
            filter_conditions=[],
        ),
    ]
    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 0), tick=False):
        await add_query_history(
            data_store_db_session,
            query_params[0],
        )
    with time_machine.travel(datetime(2024, 1, 1, 12, 0, 1), tick=False):
        await add_query_history(
            data_store_db_session,
            query_params[1],
        )

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(data_store_db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 2

        # Delete the selected row
        await pilot.press("d")
        await pilot.pause()

        # The row should be removed from the table
        assert table.row_count == 1

        # Verify the row is deleted from the DB
        list_query_history_result = await list_query_history(
            data_store_db_session, page=1, page_size=10
        )
        assert len(list_query_history_result) == 1
        query_params_removed = [row.data for row in list_query_history_result]
        assert query_params[1] not in query_params_removed
        assert query_params[0] in query_params_removed


async def test_query_history_screen_delete_all_rows(data_store_db_session):
    """Verify deleting all rows removes them from the screen and DB."""
    for i in range(5):
        with time_machine.travel(datetime(2024, 1, 1, 12, 0, i), tick=False):
            await add_query_history(
                data_store_db_session,
                QueryParameters(
                    scan_mode=False,
                    primary_key_name=f"pk{i}",
                    sort_key_name=f"sk{i}",
                    index="table",
                    key_condition=KeyCondition(partitionKeyValue=str(i)),
                    filter_conditions=[],
                ),
            )

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(data_store_db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 5

        # Delete all rows
        await pilot.press("c")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmDialogue)
        # Confirm the deletion
        await pilot.press("y")
        await pilot.pause()

        # The table should be empty
        assert table.row_count == 0

        # Verify all rows are deleted from the DB
        async with data_store_db_session.execute(
            "SELECT COUNT(*) FROM data_store WHERE record_type = ?",
            (RecordType.QueryHistory.value,),
        ) as cursor:
            row = await cursor.fetchone()
            assert len(row) == 1
            assert row[0] == 0


async def test_query_history_screen_no_data(data_store_db_session):
    """Verify the screen handles no query history gracefully."""

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session
            self.params = None

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    async with TestApp(data_store_db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 0

        # Pressing enter should not fail even with no rows
        await pilot.press("enter")
        await pilot.pause(0.05)

        # The screen should have been dismissed and returned None
        assert pilot.app.params is None
