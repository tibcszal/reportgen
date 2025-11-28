from __future__ import annotations

import argparse
import pathlib

from .config_store import default_config_path


def _abs_path(value: str | pathlib.Path) -> pathlib.Path:
    """Expand user/relative paths to absolute Path objects."""
    return pathlib.Path(value).expanduser().resolve()


def parse_args():
    parser = argparse.ArgumentParser(description="API performance report generator")
    parser.add_argument("-g", "--generator", choices=["jmeter", "k6"], required=True)
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        default=_abs_path(default_config_path()),
        type=_abs_path,
        help="Path to config.json (default: packaged config)",
    )
    parser.add_argument(
        "-r",
        "--results_dir",
        required=True,
        type=_abs_path,
        help="Directory containing the results CSV and resource usage JSON files.",
    )
    # Not required since dry runs may not produce an output file
    parser.add_argument("-o", "--output", required=False, type=_abs_path)
    parser.add_argument(
        "-p",
        "--plots_dir",
        required=False,
        default=_abs_path("plots"),
        type=_abs_path,
        help="Directory to save generated plot images (default: ./plots)",
    )
    parser.add_argument("-d", "--dry-run", required=False, action="store_true")
    return parser.parse_args()
