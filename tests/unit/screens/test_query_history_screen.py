import asyncio
from datetime import datetime

import pytest

from textual.app import App
from textual.widgets import DataTable

from dyno_viewer.components.screens.query_history import QueryHistoryScreen
from dyno_viewer.db.models import QueryHistory
from dyno_viewer.constants import FILTER_CONDITIONS, ATTRIBUTE_TYPES
from dyno_viewer.models import KeyCondition, QueryParameters, FilterCondition
import simplejson as json

from dyno_viewer.models import QueryParameters




async def test_query_history_screen_populates_from_db(db_session):
    """Ensure the screen reads query history rows from the DB and displays them."""

    # Build three sample QueryHistory rows
    async with db_session.begin():

        # created_at descending should show row3 first
        db_session.add_all(
            [
                QueryHistory(
                    table_name="tbl",
                    scan_mode=False,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=KeyCondition(partitionKeyValue="A").model_dump_json(),
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
                QueryHistory(
                    table_name="tbl",
                    scan_mode=True,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=None,
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, 1),
                ),
                QueryHistory(
                    table_name="tbl",
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

    class TestApp(App):
        CSS = ""

        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryScreen())

    async with TestApp(db_session).run_test() as pilot:
        # allow background worker to complete
        await pilot.pause(0.05)
        screen = pilot.app.screen
        assert isinstance(screen, QueryHistoryScreen)
        table = screen.query_one(DataTable)
        assert table.row_count == 3
        # Ensure ordering is newest first (created_at descending)
        first_row = table.get_row_at(0)
        last_row = table.get_row_at(2)
        assert first_row == ["2024-01-01 12:00:02", False, "pk = 'B'", ""]
        assert last_row == ["2024-01-01 12:00:00", False, "pk = 'A'", ""]


async def test_query_history_screen_with_filters(db_session):
    """Ensure the screen reads query history rows with filter conditions from the DB and displays them."""

    # Build a sample QueryHistory row with filter conditions
    async with db_session.begin():
        db_session.add(
            QueryHistory(
                table_name="tbl",
                scan_mode=False,
                primary_key_name="pk",
                sort_key_name="sk",
                index="table",
                key_condition=KeyCondition(partitionKeyValue="A").model_dump_json(),
                filter_conditions=json.dumps(
                    [
                        FilterCondition(
                            attrValue="active",
                            attrCondition=FILTER_CONDITIONS[0],
                            attrName="status",
                            attrType=ATTRIBUTE_TYPES[0],
                        ).model_dump()
                    ]
                ),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        )

    await db_session.commit()

    class TestApp(App):
        CSS = ""

        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryScreen())

    async with TestApp(db_session).run_test() as pilot:
        # allow background worker to complete
        await pilot.pause(0.05)
        screen = pilot.app.screen
        assert isinstance(screen, QueryHistoryScreen)
        table = screen.query_one(DataTable)
        assert table.row_count == 1
        first_row = table.get_row_at(0)
        assert first_row == [
            "2024-01-01 12:00:00",
            False,
            "pk = 'A'",
            "status = 'active'",
        ]


async def test_query_history_screen_pagination(db_session):
    """Verify pagination increments next_page until total_pages is reached."""

    # Insert 40 rows (page_size is 20) so we expect two pages
    async with db_session.begin():
        for i in range(40):
            db_session.add(
                QueryHistory(
                    table_name="tbl",
                    scan_mode=False,
                    primary_key_name="pk",
                    sort_key_name="sk",
                    index="table",
                    key_condition=KeyCondition(
                        partitionKeyValue=str(i)
                    ).model_dump_json(),
                    filter_conditions="[]",
                    created_at=datetime(2024, 1, 1, 12, 0, i % 60),
                )
            )
    await db_session.commit()

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryScreen())

    async with TestApp(db_session).run_test() as pilot:
        screen: QueryHistoryScreen = pilot.app.screen  # type: ignore
        await pilot.pause()
        table = screen.query_one(DataTable)
        # After initial load only first 20 rows should be present
        assert table.row_count == 20
        assert screen.next_page == 2
        assert screen.total_pages == 2

        # Trigger next page via action
        await pilot.press("n")
        await pilot.pause()
        assert table.row_count == 40
        assert screen.next_page == 2  # Should not increment beyond total_pages


async def test_query_history_screen_row_selection(db_session):
    """Verify selecting a row returns the correct QueryParameters."""

    # Insert a sample QueryHistory row
    async with db_session.begin():
        db_session.add(
            QueryHistory(
                table_name="tbl",
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
            self.push_screen(QueryHistoryScreen(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    async with TestApp(db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryScreen = pilot.app.screen  # type: ignore
        table = screen.query_one(DataTable)
        assert table.row_count == 1

        # Select the first (and only) row
        await pilot.press("enter")
        await asyncio.sleep(0.05)

        # The screen should have been dismissed and returned QueryParameters

        assert pilot.app.params is not None
        assert isinstance(pilot.app.params, QueryParameters)
        assert pilot.app.params.table_name == "tbl"
        assert pilot.app.params.scan_mode is False
        assert pilot.app.params.primary_key_name == "pk"
        assert pilot.app.params.sort_key_name == "sk"
        assert pilot.app.params.key_condition == KeyCondition(partitionKeyValue="A")
        assert pilot.app.params.filter_conditions == []


async def test_query_history_screen_no_data(db_session):
    """Verify the screen handles no query history gracefully."""

    class TestApp(App):
        def __init__(self, db_session):
            super().__init__()
            self.db_session = db_session
            self.params = None

        async def on_mount(self):  # type: ignore[override]
            self.push_screen(QueryHistoryScreen(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    async with TestApp(db_session).run_test() as pilot:
        await pilot.pause(0.05)
        screen: QueryHistoryScreen = pilot.app.screen  # type: ignore
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
                table_name="tbl",
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
            self.push_screen(QueryHistoryScreen(), callback=self.save_params)

        def save_params(self, p):
            self.params = p

    with pytest.raises(Exception, match="1 validation error for KeyCondition"):
        async with TestApp(db_session).run_test() as pilot:
            await pilot.pause(0.05)
            screen: QueryHistoryScreen = pilot.app.screen  # type: ignore
            table = screen.query_one(DataTable)
            assert table.row_count == 1

            # Select the first (and only) row
            await pilot.press("enter")
            await asyncio.sleep(0.05)

            # The screen should have been dismissed and returned None due to JSON error
            assert pilot.app.params is None
