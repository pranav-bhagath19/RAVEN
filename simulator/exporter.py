"""
RAVEN Dataset Exporter

Handles deterministic JSON serialization and dataset export.
Ensures stable key ordering and formatting without business logic side-effects.
"""

import json
from pathlib import Path
from typing import Any


def export_dataset(dataset_dict: dict[str, Any], filepath: str | Path) -> Path:
    """
    Exports dataset dictionary to a JSON file using stable, deterministic key sorting.
    Returns absolute Path object of written dataset file.
    """
    target_path = Path(filepath).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    json_str = json.dumps(dataset_dict, indent=2, sort_keys=True, separators=(",", ": "))

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(json_str + "\n")

    return target_path
