import uuid
from enum import Enum
from functools import reduce
from operator import and_
from pathlib import Path
from typing import Any, TypedDict

import yaml
from boto3.dynamodb.conditions import Attr, ConditionBase, Key
from pydantic import BaseModel, Field, computed_field, field_validator
from textual.screen import Screen

from dyno_viewer.aws.ddb import (
    convert_filter_exp_attr_cond,
    convert_filter_exp_key_cond,
    convert_filter_exp_value,
)
from dyno_viewer.constants import (
    ATTRIBUTE_TYPES,
    CONFIG_DIR_NAME,
    FILTER_CONDITIONS,
    SORT_KEY_CONDITIONS,
)
from dyno_viewer.util.path import ensure_config_dir


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


class SavedQuery(QueryParameters):
    name: str
    description: str


class QueryHistory(QueryParameters):
    table: str | None = None
    session_id: str | None = None

    def to_query_params(self) -> QueryParameters:
        return QueryParameters(
            draft=self.draft,
            filter_conditions=self.filter_conditions,
            index=self.index,
            key_condition=self.key_condition,
            next_token=self.next_token,
            primary_key_name=self.primary_key_name,
            scan_mode=self.scan_mode,
            sort_key_name=self.sort_key_name,
        )


class Config(BaseModel):
    page_size: int = Field(default=20, description="number of items per page")
    theme: str = Field(default="textual-dark", description="theme of the application")
    load_last_query_on_startup: bool = Field(
        default=True, description="load the last query when the application starts"
    )
    startup_session_group: str | None = Field(
        default=None, description="load a session group when the application starts"
    )

    @classmethod
    def load_config(cls) -> "Config":
        app_path = ensure_config_dir(CONFIG_DIR_NAME)
        config_file_path = app_path / "config.yaml"
        if config_file_path.exists():
            config_file = yaml.safe_load(config_file_path.read_bytes())
            return cls.model_validate(config_file)
        config = cls()
        config.save_config()
        return config

    def save_config(self) -> None:
        app_path = ensure_config_dir(CONFIG_DIR_NAME)
        config_file_path = app_path / "config.yaml"
        config_file_path.write_text(yaml.safe_dump(self.model_dump()), encoding="utf-8")


class Session(BaseModel):
    name: str
    aws_profile: str | None = None
    table_name: str
    aws_region: str
    session_id: str = Field(default_factory=lambda: f"table_{uuid.uuid4()}")
    session_group_id: str

    @classmethod
    def from_table_viewer_screen(
        cls, table_viewer: Screen, session_group_id: str, screen_name: str
    ) -> "Session":
        """
        Create a new instance of the `WorkspaceSession` class based on the information from a `TableViewer` screen.

        :param table_viewer: TablesViewer object (typed as base type `Screen` due to circular imports)
        :type table_viewer: Screen
        :param session_group_id: the ID of the session group that this session is part of
        :type session_group_id: str
        :param screen_name: the name of the screen
        :type screen_name: str
        :return: a new `WorkspaceSession` instance
        :rtype: WorkspaceSession
        """
        return cls(
            name=screen_name,
            aws_profile=table_viewer.aws_profile,
            table_name=table_viewer.table_name,
            aws_region=table_viewer.aws_region,
            session_id=table_viewer.id,
            session_group_id=session_group_id,
        )


class SessionGroup(BaseModel):
    name: str
    session_group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class SelectedSessionGroup(BaseModel):
    session_group: SessionGroup | None = None


class SelectedScreen(BaseModel):

    screen_name: str | None = None
