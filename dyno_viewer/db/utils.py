from typing import Any, List


from dyno_viewer.db.models import (
    JsonPathNode,
)


def json_path_from_dict(data: dict[str, Any]) -> List[JsonPathNode]:
    """
    Generate JSON paths from a nested dictionary.

    :param data: Input dictionary
    :type data: dict[str, Any]
    :return: List of JSON paths
    :rtype: List[JsonPathNode]
    """

    def walk(obj: dict[str, Any], prefix: str) -> List[JsonPathNode]:
        paths = []
        for key, value in obj.items():
            current = f"{prefix}.{key}"
            if isinstance(value, dict):
                paths.extend(walk(value, current))
            else:
                paths.append(JsonPathNode(path=current, value=current))
        return paths

    if not isinstance(data, dict):
        return []
    return walk(data, "$")
