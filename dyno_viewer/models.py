from enum import Enum
from functools import reduce
from operator import and_
from pathlib import Path
from typing import Any, TypedDict

from boto3.dynamodb.conditions import Attr, ConditionBase, Key
from pydantic import BaseModel, computed_field, field_validator

from dyno_viewer.aws.ddb import (
    convert_filter_exp_attr_cond,
    convert_filter_exp_key_cond,
    convert_filter_exp_value,
)
from dyno_viewer.constants import (
    ATTRIBUTE_TYPES,
    FILTER_CONDITIONS,
    SORT_KEY_CONDITIONS,
)


class OutputFormat(Enum):
    CSV = "csv"
    JSON = "json"


class FileToSave(BaseModel):
    path: str | Path
    file_format: OutputFormat


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
    primary_key_name: str
    sort_key_name: str
    index: str = "table"
    key_condition: KeyCondition | None = None
    filter_conditions: list[FilterCondition] = []
    next_token: str | dict | None = None
    draft: bool = False

    @computed_field
    @property
    def boto_params(self) -> dict:
        params = (
            {}
            if self.scan_mode
            else {"KeyConditionExpression": self._boto_key_condition()}
        )
        if self.filter_conditions:
            params["FilterExpression"] = self._boto_filter_condition()
        if self.index != "table":
            params["IndexName"] = self.index
        if self.next_token:
            params["ExclusiveStartKey"] = self.next_token
        return params

    def _boto_key_condition(self) -> Key | ConditionBase:
        return (
            Key(self.primary_key_name).eq(self.key_condition.partitionKeyValue)
            & convert_filter_exp_key_cond(
                self.key_condition.sortKey.attrCondition,
                self.sort_key_name,
                self.key_condition.sortKey.attrValue,
            )
            if self.key_condition.sortKey
            else Key(self.primary_key_name).eq(self.key_condition.partitionKeyValue)
        )

    def _boto_filter_condition(self) -> Attr | ConditionBase | None:
        if not self.filter_conditions:
            return None
        filter_expressions = [
            convert_filter_exp_attr_cond(
                condition.attrCondition,
                condition.attrName,
                convert_filter_exp_value(condition.attrValue, condition.attrType),
            )
            for condition in self.filter_conditions
        ]

        return reduce(and_, filter_expressions)

    @classmethod
    @field_validator("keyCondition", mode="after")
    def validate_key_condition(cls, v: KeyCondition | None) -> KeyCondition | None:
        if cls.scan_mode and v:
            raise ValueError(
                "Key condition cannot be set when scan mode is enabled. "
                "Scan mode does not support key conditions."
            )
        if not cls.scan_mode and not v:
            raise ValueError(
                "Key condition must be set when scan mode is disabled. "
                "Key conditions are required for query operations."
            )
        return v


class SavedQuery(BaseModel):
    name: str
    description: str
