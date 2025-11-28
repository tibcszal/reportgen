from __future__ import annotations

import json
import pathlib
from typing import Any, Optional

_cached_config: dict[str, Any] | None = None


def default_config_path() -> pathlib.Path:
    """Return the bundled config.json path that ships with the package."""
    return pathlib.Path(__file__).with_name("config.json")


_config_path: pathlib.Path = default_config_path()


def load_config(path: Optional[str | pathlib.Path] = None) -> dict[str, Any] | None:
    """Load and cache config from the given path (defaults to local config.json)."""
    global _cached_config, _config_path
    if path is not None:
        _config_path = pathlib.Path(path)
    if _cached_config is not None and path is None:
        return _cached_config
    with _config_path.open("r", encoding="utf-8") as f:
        _cached_config = json.load(f)
    return _cached_config


def get_config() -> dict[str, Any]:
    """Return cached config, loading from the last known path if needed."""
    if _cached_config is None:
        load_config()
    assert _cached_config is not None
    return _cached_config


def get_config_value(key: str, default: Any = None) -> Any:
    """Convenience accessor for a single config value."""
    return get_config().get(key, default)
