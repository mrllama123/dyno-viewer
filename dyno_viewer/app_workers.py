from textual.message import Message
from textual import work
from textual.worker import get_current_worker
from textual import log

from dyno_viewer.aws.ddb import query_items, scan_items


class UpdateDynDataTable(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()


@work(exclusive=True, group="update_dyn_table_info")
def update_dyn_table_info(app) -> None:
    worker = get_current_worker()
    if not worker.is_cancelled:
        log.info(f"updating table info")
        log.info("key schema=", app.table_client.key_schema)
        log.info("gsi schema=", app.table_client.global_secondary_indexes)
        main_keys = {
            ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                "AttributeName"
            ]
            for key in app.table_client.key_schema
        }

        gsi_keys = {
            gsi["IndexName"]: {
                ("primaryKey" if key["KeyType"] == "HASH" else "sortKey"): key[
                    "AttributeName"
                ]
                for key in gsi["KeySchema"]
            }
            for gsi in app.table_client.global_secondary_indexes or []
        }

        def update(self, main_keys, gsi_keys):
            self.table_info = {"keySchema": main_keys, "gsi": gsi_keys}

        app.call_from_thread(update, app, main_keys, gsi_keys)


@work(exclusive=True, group="dyn_table_query")
def dyn_table_query(app, dyn_query_params, update_existing=False):
    worker = get_current_worker()
    if not worker.is_cancelled:
        log("dyn_params=", app.dyn_query_params)
        result, next_token = (
            query_items(
                app.table_client,
                paginate=False,
                Limit=50,
                **dyn_query_params,
            )
            if "KeyConditionExpression" in dyn_query_params
            else scan_items(
                app.table_client,
                paginate=False,
                Limit=50,
                **dyn_query_params,
            )
        )

        app.post_message(UpdateDynDataTable(result, next_token, update_existing))
