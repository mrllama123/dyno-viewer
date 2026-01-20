# DynamoDB query condition operators for sort key filtering
from dyno_viewer.util.path import get_user_config_dir


SORT_KEY_CONDITIONS = [
    "==",
    ">",
    "<",
    "<=",
    ">=",
    "between",
    "begins_with",
]

# DynamoDB filter expression condition operators
FILTER_CONDITIONS = [
    "==",
    ">",
    "<",
    "<=",
    ">=",
    "!=",
    "between",
    "in",
    "attribute_exists",
    "attribute_not_exists",
    "attribute_type",
    "begins_with",
    "contains",
    "size",
]

# DynamoDB attribute data types
ATTRIBUTE_TYPES = [
    "string",
    "number",
    "binary",
    "boolean",
    "map",
    "list",
    "set",
]

CONFIG_DIR_NAME = "dyno-viewer"

DATABASE_FILE_PATH = (
    get_user_config_dir(CONFIG_DIR_NAME) / "data-store.db"
)
