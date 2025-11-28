from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any

from .config_store import get_storage_path

History = dict[str, dict[str, str]]


def load_history(path: pathlib.Path | None = None) -> History:
    """Load existing history file if present."""
    target = path or get_storage_path()
    if not target.exists():
        return {}
    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def save_history(history: History, path: pathlib.Path | None = None) -> None:
    target = path or get_storage_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=True)


def append_verdicts(analysis_results: list[dict[str, Any]], path: pathlib.Path | None = None) -> History:
    """Append current run verdicts to history and return updated history."""
    history = load_history(path)
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    for result in analysis_results:
        verdict = result.get("verdict")
        test_name = result.get("test_name")
        if verdict is None or test_name is None:
            continue
        key = str(test_name)
        history.setdefault(key, {})
        history[key][timestamp] = str(verdict)
    save_history(history, path)
    return history
