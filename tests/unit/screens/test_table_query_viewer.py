import pytest
from textual import on, work
from textual.app import App, log
from textual.reactive import reactive
from dyno_viewer.app_types import TableInfo
from dyno_viewer.components.screens.profile_select import ProfileSelectScreen
from dyno_viewer.components.screens.query import QueryScreen
from dyno_viewer.components.screens.region_select import RegionSelectScreen
from dyno_viewer.components.screens.table_select import TableSelectScreen
from dyno_viewer.components.table import DataTableManager
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import Footer
from textual.message import Message
from textual.worker import get_current_worker

from dyno_viewer.aws.ddb import (
    get_ddb_client,
    query_items,
    scan_items,
    table_client_exist,
)


class UpdateDynDataTable(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


class UpdateDynTableInfo(Message):
    def __init__(self, table_info: TableInfo) -> None:
        self.table_info = table_info
        super().__init__()


class QueryTableViewer(Screen):

    BINDINGS = [("q", "push_screen_query", "Query")]

    SCREENS = {
        "query": QueryScreen(),
        "tableSelect": TableSelectScreen(),
    }

    table_info = reactive(None)
    aws_region = reactive("ap-southeast-2")
    dyn_query_params = reactive({})
    dyn_client = reactive(None)
    # set always_update=True because otherwise textual thinks that the client hasn't changed when it actually has :(
    table_client = reactive(None, always_update=True)
    table_name = reactive("")

    def compose(self):
        yield DataTableManager()
        yield Footer()

    def update_table_client(self):
        if self.table_name != "":
            log.info(f"updating table client with profile {self.aws_profile}")
            new_table_client = table_client_exist(
                self.table_name, self.aws_region, self.aws_profile
            )
            if new_table_client:
                self.table_client = new_table_client

    def set_pagination_token(self, next_token: str | None) -> None:
        if next_token:
            self.dyn_query_params["ExclusiveStartKey"] = next_token
        else:
            self.dyn_query_params.pop("ExclusiveStartKey", None)

        # worker methods

    @work(exclusive=True, group="update_dyn_table_info", thread=True)
    def get_dyn_table_info(self) -> None:
        worker = get_current_worker()
        if not worker.is_cancelled:
            # temp disable logging doesn't work
            self.log("updating table info")
            self.log("key schema=", self.table_client.key_schema)
            self.log("gsi schema=", self.table_client.global_secondary_indexes)
            main_keys = {
                ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                    "AttributeName"
                ]
                for key in self.table_client.key_schema
            }

            gsi_keys = {
                gsi["IndexName"]: {
                    ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                        "AttributeName"
                    ]
                    for key in gsi["KeySchema"]
                }
                for gsi in self.table_client.global_secondary_indexes or []
            }

            self.post_message(
                UpdateDynTableInfo({"keySchema": main_keys, "gsi": gsi_keys})
            )

    @work(exclusive=True, group="dyn_table_query", thread=True)
    def run_table_query(self, dyn_query_params, update_existing=False):
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.log("dyn_params=", dyn_query_params)
            result, next_token = (
                query_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **dyn_query_params,
                )
                if "KeyConditionExpression" in dyn_query_params
                else scan_items(
                    self.table_client,
                    paginate=False,
                    Limit=50,
                    **dyn_query_params,
                )
            )

            self.post_message(UpdateDynDataTable(result, next_token, update_existing))




    @on(UpdateDynTableInfo)
    async def update_table_info(self, update: UpdateDynTableInfo) -> None:
        self.table_info = update.table_info

    async def on_region_select_screen_region_selected(
        self, selected_region: RegionSelectScreen.RegionSelected
    ) -> None:
        self.aws_region = selected_region.region
        self.dyn_client = get_ddb_client(selected_region.region, self.aws_profile)
        self.update_table_client()

    # async def on_table_select_screen_table_name(
    #     self,
    #     new_table_name: TableSelectScreen.TableName,
    # ) -> None:
    #     if self.table_name != new_table_name:
    #         self.table_name = new_table_name.table
    #         self.update_table_client()

    # async def on_profile_select_screen_profile_selected(
    #     self, selected_profile: ProfileSelectScreen.ProfileSelected
    # ) -> None:
    #     self.aws_profile = selected_profile.profile
    #     log.info(f"{self.aws_profile} profile selected")
    #     self.dyn_client = get_ddb_client(
    #         region_name=self.aws_region, profile_name=self.aws_profile
    #     )
    #     self.update_table_client()

    async def on_query_screen_run_query(self, run_query: QueryScreen.RunQuery) -> None:
        params = (
            {"KeyConditionExpression": run_query.key_cond_exp}
            if run_query.key_cond_exp
            else {}
        )

        if run_query.filter_cond_exp:
            params["FilterExpression"] = run_query.filter_cond_exp

        if run_query.index != "table":
            params["IndexName"] = run_query.index

        self.dyn_query_params = params
        self.run_table_query(params)

    # async def on_update_dyn_data_table(self, update_data: UpdateDynDataTable) -> None:
    #     table = self.query_one(DataDynTable)
    #     if update_data.update_existing_data:
    #         table.add_dyn_data_existing(update_data.data)
    #         self.set_pagination_token(update_data.next_token)
    #     else:
    #         table.add_dyn_data(self.table_info, update_data.data)
    #         self.set_pagination_token(update_data.next_token)


    # action methods

    async def action_push_screen_query(self) -> None:
        if self.table_client:
            self.push_screen("query")
        else:
            self.notify("No table selected")

    # watcher methods
    async def watch_table_client(self, new_table_client) -> None:
        """update DynTable with new table data"""
        if new_table_client:
            log.info("table client changed and table found, Update table data")
            self.get_dyn_table_info()
            self.run_table_query(self.dyn_query_params)
        # else:
        #     log.info("table client changed and table not found, Clear table data")
        #     self.query_one(DataDynTable).clear()


# @pytest.fixture()
# def screen_app():
#     class ScreensApp(App[None]):
#         SCREENS = {"regionSelect": RegionSelectScreen()}

#         region = reactive("")

#         async def on_region_select_screen_region_selected(
#             self, selected_region: RegionSelectScreen.RegionSelected
#         ) -> None:
#             self.region = selected_region.region

#     return ScreensApp
