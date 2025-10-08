from pathlib import Path

import simplejson as json


def save_query_results_to_json(path: str | Path, data: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
