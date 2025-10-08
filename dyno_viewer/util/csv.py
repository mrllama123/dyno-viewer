import csv
from pathlib import Path

import simplejson as json


def save_query_results_to_csv(path: str | Path, data: list[dict]) -> None:
    fieldnames = sorted({k for item in data for k in item.keys()})

    def norm(v):
        if isinstance(v, (dict, list, set)):
            return json.dumps(list(v) if isinstance(v, set) else v)
        return v

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow({k: norm(item.get(k, "")) for k in fieldnames})
