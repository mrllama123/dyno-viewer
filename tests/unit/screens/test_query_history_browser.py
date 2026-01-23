import asyncio
from datetime import datetime
from sqlalchemy import select, func

import pytest

from textual.app import App
from textual.widgets import DataTable

from dyno_viewer.components.screens.confirm_dialogue import ConfirmDialogue
from dyno_viewer.components.screens.query_history_browser import QueryHistoryBrowser
from dyno_viewer.db.models import QueryHistory
from dyno_viewer.db.queries import add_query_history, list_query_history
from dyno_viewer.constants import FILTER_CONDITIONS, ATTRIBUTE_TYPES
from dyno_viewer.models import KeyCondition, QueryParameters, FilterCondition
import simplejson as json
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


async def test_query_history_screen_row_selection(db_session):
    """Verify selecting a row returns the correct QueryParameters."""

    # Insert a sample QueryHistory row
    async with db_session.begin():
        db_session.add(
            QueryHistory(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="A").model_dump_json(),
                filter_conditions="[]",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        )
    await db_session.commit()

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session
            self.params = None

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    async with TestApp(db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 1

        # Select the first (and only) row
        await pilot.press("enter")
        await asyncio.sleep(0.05)

        # The screen should have been dismissed and returned QueryParameters

        assert pilot.app.params is not None
        assert isinstance(pilot.app.params, QueryParameters)
        assert pilot.app.params.scan_mode is False
        assert pilot.app.params.primary_key_name == "pk"
        assert pilot.app.params.sort_key_name == "sk"
        assert pilot.app.params.key_condition == KeyCondition(partitionKeyValue="A")
        assert pilot.app.params.filter_conditions == []


async def test_query_history_screen_delete_row(db_session):
    """Verify deleting a row removes it from the screen and DB."""

    # Insert a sample QueryHistory row
    async with db_session.begin():
        db_session.add(
            QueryHistory(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="A").model_dump_json(),
                filter_conditions="[]",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        )
        db_session.add(
            QueryHistory(
                scan_mode=False,
                primary_key_name="pk2",
                sort_key_name="sk2",
                index="table2",
                key_condition=KeyCondition(partitionKeyValue="B").model_dump_json(),
                filter_conditions="[]",
                created_at=datetime(2024, 1, 1, 12, 0, 1),
            )
        )
    await db_session.commit()

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(db_session).run_test() as pilot:
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
        total = await db_session.scalar(
            select(func.count()).select_from(  # pylint: disable=not-callable
                QueryHistory
            )
        )

        assert total == 1


async def test_query_history_screen_delete_all_rows(db_session):
    """Verify deleting all rows removes them from the screen and DB."""

    # Insert sample QueryHistory rows
    async with db_session.begin():
        for i in range(5):
            db_session.add(
                QueryHistory(
                    scan_mode=False,
                    primary_key_name=f"pk{i}",
                    sort_key_name=f"sk{i}",
                    index="table",
                    key_condition=KeyCondition(
                        partitionKeyValue=str(i)
                    ).model_dump_json(),
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, i),
                )
            )
    await db_session.commit()

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser())

    async with TestApp(db_session).run_test() as pilot:
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
        total = await db_session.scalar(
            select(func.count()).select_from(  # pylint: disable=not-callable
                QueryHistory
            )
        )

        assert total == 0


async def test_query_history_screen_no_data(db_session):
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

    async with TestApp(db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 0

        # Pressing enter should not fail even with no rows
        await pilot.press("enter")
        await asyncio.sleep(0.05)

        # The screen should have been dismissed and returned None
        assert pilot.app.params is None


async def test_query_history_screen_invalid_json(db_session):
    """Verify the screen handles invalid JSON in DB rows gracefully."""

    # Insert a QueryHistory row with invalid JSON
    async with db_session.begin():
        db_session.add(
            QueryHistory(
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition="INVALID_JSON",
                filter_conditions="[INVALID_JSON]",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        )
    await db_session.commit()

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session
            self.params = None

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryBrowser(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    with pytest.raises(Exception, match="1 validation error for KeyCondition"):
        async with TestApp(db_session).run_test() as pilot:
            await pilot.pause(0.05)
            screen: QueryHistoryBrowser = pilot.app.screen  # type: ignore
            table = screen.query_one(DataTable)
            assert table.row_count == 1

            # Select the first (and only) row
            await pilot.press("enter")
            await asyncio.sleep(0.05)

            # The screen should have been dismissed and returned None due to JSON error
            assert pilot.app.params is None
