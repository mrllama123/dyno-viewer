# DynamoDB query condition operators for sort key filtering
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
