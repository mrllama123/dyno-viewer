import logging
import re
from decimal import Decimal

import boto3
import simplejson as json
from boto3.dynamodb.conditions import Attr, Key
from boto3.session import Session
from dynamodb_json import json_util as dyn_json

LOG_LEVEL = logging.INFO


def get_logger():
    import logging

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    return logger


logger = get_logger()


def table_client_exist(table_name, region_name, profile_name):
    try:
        client = get_table(table_name, region_name, profile_name)
        if client.table_status in ("CREATING", "UPDATING", "ACTIVE"):
            return client
        return None
    except Exception as error:
        if error.response["Error"]["Code"] in [
            "ResourceNotFoundException",
        ]:
            return None
        raise error


def get_table(table_name, region_name, profile_name):
    return get_dyn_resource(region_name, profile_name).Table(table_name)


def get_dyn_resource(region_name, profile_name):
    return (
        Session(profile_name=profile_name, region_name=region_name).resource("dynamodb")
        if profile_name
        else boto3.resource("dynamodb", region_name=region_name)
    )


def get_table_client(table, region_name="ap-southeast-2", profile_name=None):
    return (
        get_table(table, region_name, profile_name) if isinstance(table, str) else table
    )


def get_ddb_client(region_name="ap-southeast-2", profile_name=None):
    return (
        Session(profile_name=profile_name, region_name=region_name).client("dynamodb")
        if profile_name
        else boto3.client("dynamodb", region_name=region_name)
    )


def list_all_tables(client=None, paginate=True, **kwargs):
    ddb_client = client or get_ddb_client(client)
    tables = []
    result = ddb_client.list_tables(**kwargs)
    tables.extend(result["TableNames"])

    if paginate:
        while "LastEvaluatedTableName" in result:
            tables.extend(result["TableNames"])
            result = ddb_client.list_tables(
                **kwargs, ExclusiveStartTableName=result["LastEvaluatedTableName"]
            )

        return tables
    return tables, result.get("LastEvaluatedTableName")


def get_item(table, item_key, return_none=False, consistent_read=False):
    """
    Get an item using the item key.

    :param table: name or client of the dynamodb table
    :param item_key: e.g {"pk":"partition_key", "sk":"sort_key"}
    :param return_none: return None if the item doesn't exist.
    :return:
    """
    resp = get_table_client(table).get_item(
        Key=item_key, ConsistentRead=consistent_read
    )
    if not return_none:
        return resp["Item"]

    return resp.get("Item")


def get_items(table_name, item_keys, **kwargs):
    """
    Use the BatchGetItem API to bulk read items.
    """

    def make_key(key):
        return {"pk": {"S": key["pk"]}, "sk": {"S": key["sk"]}}

    items = []
    keys = [make_key(d) for d in item_keys]
    logger.info("Batch reading %s item keys.", len(keys))
    batch_size = 100  # the max ddb supports.
    batches = [keys[n : n + batch_size] for n in range(0, len(keys), batch_size)]

    client = get_ddb_client()
    request = {"RequestItems": {table_name: {"Keys": None, **kwargs}}}

    for n, batch in enumerate(batches):
        request["RequestItems"][table_name]["Keys"] = batch
        res = client.batch_get_item(**request)
        for v in res["Responses"].values():
            items.extend(v)
        logger.info("%s/%s", n, len(batches))

    return items


def query_items(
    table,
    paginate=True,
    **query_kwargs,
):
    items = []
    table_client = get_table_client(table)
    resp = table_client.query(**query_kwargs)
    items.extend(resp["Items"])
    if paginate:
        while "LastEvaluatedKey" in resp:
            resp = table_client.query(
                **query_kwargs, ExclusiveStartKey=resp["LastEvaluatedKey"]
            )
            items.extend(resp["Items"])
        return items

    return items, resp.get("LastEvaluatedKey")


def query_first(table, return_none=False, **query_kwargs):
    items = query_items(table, **query_kwargs)
    items_count = len(items)

    if items_count == 0 and return_none:
        return None

    if items_count == 0:
        raise ValueError("Item not found")

    return items[0]


def check_attr_exists(table, pk, attr, sk=None):
    """
    Check an attribute exists given a pk/sk.
    """
    return bool(
        len(
            get_table_client(table).query(
                KeyConditionExpression=Key("pk").eq(pk) & Key("sk").eq(sk),
                FilterExpression=Attr(attr).exists(),
            )["Items"]
        )
    )


def scan_items(table, paginate=True, **query_kwargs):
    """Debugging utility."""
    items = []
    table_client = get_table_client(table)
    resp = table_client.scan(**query_kwargs)
    items.extend(resp["Items"])
    if paginate:
        while "LastEvaluatedKey" in resp:
            resp = table_client.scan(
                **query_kwargs, ExclusiveStartKey=resp["LastEvaluatedKey"]
            )
            items.extend(resp["Items"])
        return items

    return items, resp.get("LastEvaluatedKey")


def covert_comparator_exp(cond, attr_name, value, is_key=True) -> Key | Attr | None:
    attr_class = Key if is_key else Attr
    if cond == "==":
        return attr_class(attr_name).eq(value)
    if cond == "!=":
        return attr_class(attr_name).ne(value)
    if cond == ">=":
        return attr_class(attr_name).gte(value)
    if cond == ">":
        return attr_class(attr_name).gt(value)
    if cond == "<=":
        return attr_class(attr_name).lte(value)
    if cond == "<":
        return attr_class(attr_name).lt(value)

    return None


def convert_filter_exp_key_cond(cond, attr_name, value) -> Key:
    comparator = covert_comparator_exp(cond, attr_name, value)

    if comparator:
        return comparator

    if cond == "between":
        return Key(attr_name).between(value[0], value[1])
    if cond == "begins_with":
        return Key(attr_name).begins_with(value)

    raise ValueError("passed incorrect condition for key filter expression")


def convert_filter_exp_attr_cond(cond, attr_name, value=None) -> Attr:
    comparator = covert_comparator_exp(cond, attr_name, value, is_key=False)

    if comparator:
        return comparator

    if cond == "between":
        return Attr(attr_name).between(value[0], value[1])
    if cond == "begins_with":
        return Attr(attr_name).begins_with(value)
    if cond == "in":
        return Attr(attr_name).is_in(value)
    if cond == "attribute_exists":
        return Attr(attr_name).exists()
    if cond == "attribute_not_exists":
        return Attr(attr_name).not_exists()
    if cond == "attribute_type":
        return Attr(attr_name).attribute_type(value)
    if cond == "contains":
        return Attr(attr_name).contains(value)
    if cond == "size":
        return Attr(attr_name).size()

    raise ValueError("passed incorrect condition for key filter expression")


def convert_filter_exp_value(value: str, type: str):
    if type == "number":
        return Decimal(value)
    if type == "list":
        return list(value)
    if type == "map":
        return json.loads(value)
    if type == "boolean":
        return bool(value)
    if type == "set":
        value_formatted = re.sub(r"[\(\)]", "", value)
        return set(value_formatted.split(","))

    return value


def float_to_decimal(payload):
    return json.loads(json.dumps(payload), parse_float=Decimal)


def serialise_dynamodb_json(json_obj):
    return json.loads(dyn_json.dumps(json_obj))
