from typing_extensions import TypedDict
from boto3.dynamodb.conditions import Attr, Key

QueryResult = TypedDict(
    "QueryResult",
    {"KeyConditionExpression": Key | None, "FilterConditionExpression": Attr | None},
)
