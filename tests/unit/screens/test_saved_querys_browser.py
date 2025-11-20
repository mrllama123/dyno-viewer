import pytest
from textual import work
from textual.app import App
from textual.widgets import DataTable, Input
from textual.reactive import reactive
from dyno_viewer.components.screens.confirm_dialogue import ConfirmDialogue
from dyno_viewer.components.screens.saved_querys_browser import SavedQueryBrowser
from dyno_viewer.db.models import QueryHistory, SavedQuery
from dyno_viewer.models import QueryParameters, KeyCondition, FilterCondition
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select, func


async def test_mount_saved_queries_screen(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)


@pytest.mark.time_machine(datetime(2024, 6, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")))
async def test_populate_saved_queries_table(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=False,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=KeyCondition(
                            partitionKeyValue="customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
                            sortKeyCondition=None,
                        ),
                    ),
                    name="customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
                    description="Test saved query",
                )
            )
        await db_session.commit()
        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        table = pilot.app.screen.query_one(DataTable)
        assert table.row_count == 1

        row = table.get_row_at(0)
        assert row == [
            "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d",
            "Test saved query",
            "2024-06-01 12:00:00",
            False,
            "pk = 'customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d'",
            "",
        ]
        await pilot.press("tab", "enter")  # select the row
        await pilot.pause()
        params = pilot.app.params
        assert isinstance(params, QueryParameters)
        assert params.scan_mode is False
        assert params.primary_key_name == "pk"
        assert params.sort_key_name == "sk"
        assert (
            params.key_condition.partitionKeyValue
            == "customer#0e044201-d3ce-4ce9-99c3-594ef3f2c60d"
        )
        assert params.key_condition.sortKey is None


@pytest.mark.time_machine(datetime(2024, 6, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")))
async def test_no_saved_queries(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        table = pilot.app.screen.query_one(DataTable)
        assert table.row_count == 0


@pytest.mark.time_machine(datetime(2024, 6, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")))
async def test_empty_search_results(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=True,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=None,
                        filter_conditions=[
                            FilterCondition(
                                attrName="status",
                                attrCondition="==",
                                attrValue="active",
                                attrType="string",
                            )
                        ],
                    ),
                    name="Active Items Query",
                    description="Query for active items",
                )
            )
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=False,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=KeyCondition(
                            partitionKeyValue="customer#123", sortKeyCondition=None
                        ),
                    ),
                    name="Customer 123 Query",
                    description="Query for customer 123",
                )
            )
        await db_session.commit()
        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        screen = pilot.app.screen
        search_input = screen.query_one("#search_saved_queries", Input)
        search_input.value = "nonexistent_query"
        await search_input.action_submit()
        await pilot.pause()
        table = screen.query_one(DataTable)
        assert table.row_count == 0


@pytest.mark.time_machine(datetime(2024, 6, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")))
async def test_select_saved_query(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=True,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=None,
                        filter_conditions=[
                            FilterCondition(
                                attrName="status",
                                attrCondition="==",
                                attrValue="active",
                                attrType="string",
                            )
                        ],
                    ),
                    name="Active Items Query",
                    description="Query for active items",
                )
            )
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=False,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=KeyCondition(
                            partitionKeyValue="customer#123", sortKeyCondition=None
                        ),
                    ),
                    name="Customer 123 Query",
                    description="Query for customer 123",
                )
            )
        await db_session.commit()

        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        table = pilot.app.screen.query_one(DataTable)
        assert table.row_count == 2

        assert table.get_row_at(0) == [
            "Customer 123 Query",
            "Query for customer 123",
            "2024-06-01 12:00:00",
            False,
            "pk = 'customer#123'",
            "",
        ]
        assert table.get_row_at(1) == [
            "Active Items Query",
            "Query for active items",
            "2024-06-01 12:00:00",
            True,
            "",
            "status = 'active'",
        ]
        await pilot.press("tab", "enter")
        await pilot.pause()
        params = pilot.app.params
        assert isinstance(params, QueryParameters)
        assert not params.scan_mode
        assert params.primary_key_name == "pk"
        assert params.sort_key_name == "sk"
        assert params.key_condition
        assert params.key_condition.partitionKeyValue == "customer#123"
        assert params.key_condition.sortKey is None
        assert len(params.filter_conditions) == 0

        # Reset and test the other saved query
        await pilot.press("p")  # reopen the screen
        await pilot.pause()

        await pilot.press("tab", "down", "enter")  # select the row
        await pilot.pause()
        params = pilot.app.params
        assert isinstance(params, QueryParameters)
        assert params.scan_mode is True
        assert params.primary_key_name == "pk"
        assert params.sort_key_name == "sk"
        assert params.key_condition is None
        assert len(params.filter_conditions) == 1
        assert params.filter_conditions[0].attrName == "status"
        assert params.filter_conditions[0].attrCondition == "=="
        assert params.filter_conditions[0].attrValue == "active"
        assert params.filter_conditions[0].attrType == "string"


async def test_pagination_saved_queries(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            for i in range(100):
                db_session.add(
                    SavedQuery.from_query_params(
                        QueryParameters(
                            scan_mode=False,
                            primary_key_name="pk",
                            sort_key_name="sk",
                            key_condition=KeyCondition(
                                partitionKeyValue=f"item#{i}", sortKeyCondition=None
                            ),
                        ),
                        name=f"Item {i} Query",
                        description=f"Query for item {i}",
                    )
                )
        await db_session.commit()

        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        await pilot.press("tab")
        screen = pilot.app.screen
        table = screen.query_one(DataTable)
        assert table.row_count == 20  # assuming page size is 10

        await pilot.press("n")  # go to next page
        await pilot.pause()
        assert table.row_count == 40  # now should have 40 entries

        await pilot.press("n")  # go to next page
        await pilot.pause()
        assert table.row_count == 60  # now should have all 60 entries

        await pilot.press("n")  # go to next page
        await pilot.pause()
        assert table.row_count == 80  # now should have all 80 entries

        await pilot.press("n")  # go to next page
        await pilot.pause()
        assert table.row_count == 100  # now should have all 100 entries


async def test_delete_saved_query(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            db_session.add(
                SavedQuery.from_query_params(
                    QueryParameters(
                        scan_mode=False,
                        primary_key_name="pk",
                        sort_key_name="sk",
                        key_condition=KeyCondition(
                            partitionKeyValue="customer#delete_me",
                            sortKeyCondition=None,
                        ),
                    ),
                    name="Delete Me Query",
                    description="This query will be deleted",
                )
            )
        await db_session.commit()

        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        screen = pilot.app.screen
        table = screen.query_one(DataTable)
        assert table.row_count == 1

        await pilot.press("tab")  # focus on the table
        await pilot.press("d")  # trigger delete action
        await pilot.pause()
        # Confirm deletion
        assert isinstance(pilot.app.screen, ConfirmDialogue)
        await pilot.press("enter")
        await pilot.pause()
        assert table.row_count == 0

        # Verify all rows are deleted from the DB
        total = await db_session.scalar(
            select(func.count()).select_from(  # pylint: disable=not-callable
                QueryHistory
            )
        )

        assert total == 0


async def test_delete_all_saved_queries(db_session):
    class TestSavedQueriesScreenApp(App):
        BINDINGS = [("p", "push_saved_queries_screen", "Push Saved Queries Screen")]
        db_session = reactive(None)
        params = reactive(None)

        @work
        async def action_push_saved_queries_screen(self):
            self.params = await self.push_screen_wait(SavedQueryBrowser())

    async with TestSavedQueriesScreenApp().run_test() as pilot:
        async with db_session.begin():
            for i in range(5):
                db_session.add(
                    SavedQuery.from_query_params(
                        QueryParameters(
                            scan_mode=False,
                            primary_key_name="pk",
                            sort_key_name="sk",
                            key_condition=KeyCondition(
                                partitionKeyValue=f"item#{i}", sortKeyCondition=None
                            ),
                        ),
                        name=f"Item {i} Query",
                        description=f"Query for item {i}",
                    )
                )
        await db_session.commit()

        pilot.app.db_session = db_session
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SavedQueryBrowser)
        screen = pilot.app.screen
        table = screen.query_one(DataTable)
        assert table.row_count == 5

        await pilot.press("tab", "c")  # trigger delete all action
        await pilot.pause()
        # Confirm deletion
        assert isinstance(pilot.app.screen, ConfirmDialogue)
        await pilot.press("y")
        await pilot.pause()
        assert table.row_count == 0

        # Verify all rows are deleted from the DB
        total = await db_session.scalar(
            select(func.count()).select_from(SavedQuery)  # pylint: disable=not-callable
        )

        assert total == 0
