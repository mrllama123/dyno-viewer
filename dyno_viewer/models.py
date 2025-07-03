from typing import Any, TypedDict
from pydantic import BaseModel, field_validator
from functools import reduce
from operator import and_

from dyno_viewer.aws.ddb import (
    convert_filter_exp_key_cond,
    convert_filter_exp_attr_cond,
    convert_filter_exp_value,
)
from dyno_viewer.constants import (
    SORT_KEY_CONDITIONS,
    ATTRIBUTE_TYPES,
    FILTER_CONDITIONS,
)
from boto3.dynamodb.conditions import Key, Attr


class KeySchema(TypedDict):
    primaryKey: str
    sortKey: str


class TableInfo(TypedDict):
    tableName: str = ""
    keySchema: KeySchema
    gsi: dict[str, KeySchema]


class BaseCondition(BaseModel):
    attrType: str
    attrCondition: str
    attrValue: Any

    @field_validator("attrType")
    @classmethod
    def validate_attr_type(cls, v: str) -> str:
        if v not in ATTRIBUTE_TYPES:
            raise ValueError(
                f"Invalid attribute type: {v}, must be one of {ATTRIBUTE_TYPES}"
            )
        return v


class SortKeyCondition(BaseCondition):
    @field_validator("attrCondition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in SORT_KEY_CONDITIONS:
            raise ValueError(
                f"Invalid sort key condition: {v}, must be one of {SORT_KEY_CONDITIONS}"
            )
        return v


class KeyCondition(BaseModel):
    index: str = "table"
    partitionKeyValue: str
    sortKey: SortKeyCondition | None = None


class FilterCondition(BaseCondition):
    attrName: str

    @field_validator("attrCondition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in FILTER_CONDITIONS:
            raise ValueError(
                f"Invalid filter condition: {v}, must be one of {FILTER_CONDITIONS}"
            )
        return v


class QueryParameters(BaseModel):
    scan_mode: bool = False
    keyCondition: KeyCondition | None = None
    filterConditions: list[FilterCondition] = []

    @field_validator("keyCondition", mode="after")
    @classmethod
    def validate_key_condition(cls, v: KeyCondition | None) -> KeyCondition | None:
        if cls.scan_mode and v:
            raise ValueError(
                "Key condition cannot be set when scan mode is enabled. "
                "Scan mode does not support key conditions."
            )
        elif not cls.scan_mode and not v:
            raise ValueError(
                "Key condition must be set when scan mode is disabled. "
                "Key conditions are required for query operations."
            )
        return v

    def convert_key_condition_to_boto_key(self, table_info: TableInfo) -> Key:
        primary_key_name = (
            table_info["keySchema"]["primaryKey"]
            if self.keyCondition.index == "table"
            else table_info["gsi"][self.keyCondition.index]["primaryKey"]
        )
        sort_key_name = (
            table_info["keySchema"]["sortKey"]
            if self.keyCondition.index == "table"
            else table_info["gsi"][self.keyCondition.index]["sortKey"]
        )

        return (
            Key(primary_key_name).eq(self.keyCondition.partitionKeyValue)
            & convert_filter_exp_key_cond(
                self.keyCondition.sortKey.attrCondition,
                sort_key_name,
                self.keyCondition.sortKey.attrValue,
            )
            if self.keyCondition.sortKey
            else Key(primary_key_name).eq(self.keyCondition.partitionKeyValue)
        )

    def convert_filter_conditions_to_boto_attr(self) -> Attr | None:
        if not self.filterConditions:
            return None
        filter_expressions = [
            convert_filter_exp_attr_cond(
                condition.attrCondition,
                condition.attrName,
                convert_filter_exp_value(condition.attrValue, condition.attrType),
            )
            for condition in self.filterConditions
        ]

        return reduce(and_, filter_expressions)
