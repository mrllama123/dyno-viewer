import json
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from dyno_viewer.models import FilterCondition, KeyCondition, QueryParameters

Base = declarative_base()


class QueryBase(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_mode: Mapped[bool] = mapped_column(Boolean, nullable=False)
    primary_key_name: Mapped[str] = mapped_column(String, nullable=False)
    sort_key_name: Mapped[str] = mapped_column(String, nullable=False)
    index: Mapped[str] = mapped_column(String, nullable=False)
    key_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filter_conditions: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    next_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("UTC")),
        index=True,
    )

    def to_query_params(self) -> QueryParameters:
        return QueryParameters.model_validate(
            {
                "scan_mode": self.scan_mode,
                "primary_key_name": self.primary_key_name,
                "sort_key_name": self.sort_key_name,
                "index": self.index,
                "key_condition": (
                    KeyCondition.model_validate_json(self.key_condition)
                    if self.key_condition
                    else None
                ),
                "filter_conditions": [
                    FilterCondition.model_validate(f)
                    for f in (
                        json.loads(self.filter_conditions)
                        if self.filter_conditions
                        else []
                    )
                ],
                "next_token": self.next_token,
            }
        )


class QueryHistory(QueryBase):
    __tablename__ = "query_history"

    @classmethod
    def from_query_params(cls, params: QueryParameters) -> "QueryHistory":
        return cls(
            scan_mode=params.scan_mode,
            primary_key_name=params.primary_key_name,
            sort_key_name=params.sort_key_name,
            index=params.index,
            key_condition=(
                params.key_condition.model_dump_json() if params.key_condition else None
            ),
            filter_conditions=json.dumps(
                [f.model_dump() for f in params.filter_conditions]
            ),
        )


class SavedQuery(QueryBase):
    __tablename__ = "saved_queries"

    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @classmethod
    def from_query_params(
        cls, params: QueryParameters, name: str, description: str = ""
    ) -> "QueryHistory":
        return cls(
            name=name,
            description=description,
            scan_mode=params.scan_mode,
            primary_key_name=params.primary_key_name,
            sort_key_name=params.sort_key_name,
            index=params.index,
            key_condition=(
                params.key_condition.model_dump_json() if params.key_condition else None
            ),
            filter_conditions=json.dumps(
                [f.model_dump() for f in params.filter_conditions]
            ),
        )


class ListQueryHistoryResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    total: int
    total_pages: int
    items: list[QueryHistory]


class ListSavedQueriesResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    total: int
    total_pages: int
    items: list[SavedQuery]
