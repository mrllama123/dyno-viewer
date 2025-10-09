import json
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlmodel import Field, SQLModel

from dyno_viewer.models import QueryParameters


class QueryHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    table_name: str
    scan_mode: bool
    primary_key_name: str
    sort_key_name: str
    index: str
    key_condition: str | None = Field(default=None)  # JSON string
    filter_conditions: str = Field(default="[]")  # JSON string
    next_token: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda : datetime.now(ZoneInfo("UTC")), index=True
    )

    @classmethod
    def from_query_params(cls, params: QueryParameters) -> "QueryHistory":
        return cls(
            table_name=params.table_name,
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
