import logging
import os
import functools
import simplejson as json
from decimal import Decimal as D

import boto3
from boto3.dynamodb.conditions import Attr, Key
from dynamodb_json import json_util as dyn_json

from boto3.session import Session
from botocore.exceptions import ClientError


LOG_LEVEL = logging.INFO


def get_logger():
    import logging

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    return logger


logger = get_logger()

AWSHELPER_FORCE_USE_ISO = bool(os.getenv("AWSHELPER_FORCE_USE_ISO", False))


def batch(payloads, max_submit):
    """batch payload items to get over api limits"""
    for i in range(0, len(payloads), max_submit):
        yield payloads[i : i + max_submit]


def get_table(table_name, region_name, profile_name):
    client = get_dyn_resource(region_name, profile_name).Table(table_name)
    try:
        if client.table_status in ("CREATING", "UPDATING", "ACTIVE"):
            return client
    except ClientError as error:
        if error.response['Error']['Code'] == "ResourceNotFoundException":
            return None
        raise
    except Exception:
        raise
    


def get_dyn_resource(region_name, profile_name):
    return Session(profile_name=profile_name).resource(
        "dynamodb", region_name=region_name
    )


def get_table_client(table, region_name="ap-southeast-2", profile_name="default"):
    return (
        get_table(table, region_name, profile_name) if isinstance(table, str) else table
    )


def get_ddb_client(client=None, region_name="ap-southeast-2", profile_name="default"):
    return (
        client
        if client
        else Session(profile_name=profile_name).client(
            "dynamodb", region_name=region_name
        )
    )


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
    else:
        return resp.get("Item")


def get_items(table_name, item_keys, return_none=False, **kwargs):
    """
    Use the BatchGetItem API to bulk read items.
    """

    def make_key(key):
        return {"pk": {"S": key["pk"]}, "sk": {"S": key["sk"]}}

    items = []
    keys = [make_key(d) for d in item_keys]
    logger.info(f"Batch reading {len(keys)} item keys.")
    batch_size = 100  # the max ddb supports.
    batches = [keys[n : n + batch_size] for n in range(0, len(keys), batch_size)]

    client = get_ddb_client()
    request = {"RequestItems": {table_name: {"Keys": None, **kwargs}}}

    for n, batch in enumerate(batches):
        request["RequestItems"][table_name]["Keys"] = batch
        res = client.batch_get_item(**request)
        for k, v in res["Responses"].items():
            items.extend(v)
        logger.info(f"{n}/{len(batches)}")

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
        raise Exception(f"Item not found")

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


def float_to_decimal(payload):
    return json.loads(json.dumps(payload), parse_float=D)


def serialise_dynamodb_json(json_obj):
    return json.loads(dyn_json.dumps(json_obj))
