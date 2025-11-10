from __future__ import annotations

from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import math
import os


def _build_uniform_time_series(data_map: List[float]) -> tuple[list[int], list[float]]:
    seconds: list[int] = list(range(1, len(data_map)))
    values: list[float] = []
    for sec in seconds:
        values.append(data_map[sec - 1])
    return seconds, values


def plot_tps_over_time(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    tps_by_second: Dict[int, float] = result.get("transaction_count_per_second", {})
    duration = int(result.get("test_duration_in_seconds", len(tps_by_second)))
    if duration <= 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No duration", ha="center", va="center")
        ax.set_axis_off()
        return fig
    seconds, tps_values = _build_uniform_time_series(list(tps_by_second.values()))
    fig, ax = plt.subplots(figsize=(8, 4))
    marker_style = "o" if duration <= 120 else None
    ax.plot(seconds, tps_values, marker=marker_style, linewidth=1.4)
    ax.set_xlim(1, duration)
    ax.set_xlabel("Second")
    ax.set_ylabel("Transactions")
    ax.set_title(title or f"TPS Over Time: {result.get('test_name', 'unknown')}")
    ax.grid(True, linestyle="--", alpha=0.4)
    return fig


def plot_errors_over_time(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    err_map: Dict[int, int] = result.get("error_count_per_second", {})
    duration = int(result.get("test_duration_in_seconds", len(err_map)))
    if duration <= 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No duration", ha="center", va="center")
        ax.set_axis_off()
        return fig
    seconds, err_values = _build_uniform_time_series(list(err_map.values()))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(seconds, err_values, color="#d9534f")
    ax.set_xlim(1, duration)
    ax.set_xlabel("Second")
    ax.set_ylabel("Errors")
    ax.set_title(title or f"Errors Over Time: {result.get('test_name', 'unknown')}")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    return fig


def plot_response_times_by_api(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    max_map: Dict[str, int] = result.get("maximum_response_time_per_api", {})
    min_map: Dict[str, int] = result.get("minimum_response_time_per_api", {})
    avg_map: Dict[str, float] = result.get("average_response_time_per_api", {})

    apis = sorted(set(max_map.keys()) | set(min_map.keys()) | set(avg_map.keys()))
    if not apis:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No response time data", ha="center", va="center")
        ax.set_axis_off()
        return fig

    max_vals = [max_map.get(a, math.nan) for a in apis]
    min_vals = [min_map.get(a, math.nan) for a in apis]
    avg_vals = [avg_map.get(a, math.nan) for a in apis]

    x = range(len(apis))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(8, len(apis) * 0.6), 5))
    ax.bar([i - width for i in x], min_vals, width=width, label="Min", color="#5cb85c")
    ax.bar(x, avg_vals, width=width, label="Avg", color="#5bc0de")
    ax.bar([i + width for i in x], max_vals, width=width, label="Max", color="#f0ad4e")

    ax.set_xticks(list(x))
    ax.set_xticklabels(apis, rotation=45, ha="right")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title(
        title or f"Response Times by API: {result.get('test_name', 'unknown')}"
    )
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    return fig


def plot_error_rate_by_api(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    tx_map: Dict[str, int] = result.get("transaction_count_per_api", {})
    err_map: Dict[str, int] = result.get("error_count_per_api", {})
    apis = sorted(set(tx_map.keys()) | set(err_map.keys()))
    if not apis:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No API transaction/error data", ha="center", va="center")
        ax.set_axis_off()
        return fig

    rates = [
        (err_map.get(a, 0) / tx_map.get(a, 1)) if tx_map.get(a, 0) > 0 else 0.0
        for a in apis
    ]

    fig, ax = plt.subplots(figsize=(max(8, len(apis) * 0.6), 4))
    ax.bar(apis, rates, color="#d9534f")
    ax.set_ylabel("Error Rate")
    ax.set_title(title or f"Error Rate by API: {result.get('test_name', 'unknown')}")
    ax.set_xticklabels(apis, rotation=45, ha="right")
    ax.set_ylim(0, max(rates) * 1.15 if rates else 1)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    return fig


def plot_comparison_tps(
    results: List[Dict[str, Any]], *, title: str = "TPS Comparison"
) -> Figure:
    if not results:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No results provided", ha="center", va="center")
        ax.set_axis_off()
        return fig
    max_duration = max(int(r.get("test_duration_in_seconds", 0)) for r in results)
    fig, ax = plt.subplots(figsize=(9, 5))
    for r in results:
        tps_map: Dict[int, float] = r.get("transaction_count_per_second", {})
        seconds, tps_values = _build_uniform_time_series(list(tps_map.values()))
        marker_style = "o" if max_duration <= 120 else None
        ax.plot(
            seconds,
            tps_values,
            marker=marker_style,
            linewidth=1.1,
            label=r.get("test_name", "unknown"),
        )
    ax.set_xlim(1, max_duration)
    ax.set_xlabel("Second")
    ax.set_ylabel("Transactions")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    return fig


def save_figure(fig: Figure, directory: str, name: str, *, fmt: str = "png") -> str:
    os.makedirs(directory, exist_ok=True)
    safe = name.strip().lower().replace(" ", "_").replace("/", "_").replace(".", "_")
    file_path = os.path.join(directory, f"{safe}.{fmt}")
    fig.savefig(file_path, format=fmt, bbox_inches="tight")
    return file_path


def create_and_save_graphs(
    analysis_results: List[Dict[str, Any]], plots_dir: str
) -> None:
    os.makedirs(plots_dir, exist_ok=True)

    for result in analysis_results:
        test_name = result.get("test_name", "unknown")
        figures: list[tuple[Figure, str]] = [
            (plot_tps_over_time(result), f"{test_name}_tps_over_time"),
            (plot_errors_over_time(result), f"{test_name}_errors_over_time"),
            (plot_response_times_by_api(result), f"{test_name}_response_times_by_api"),
            (plot_error_rate_by_api(result), f"{test_name}_error_rate_by_api"),
        ]
        for fig, filename in figures:
            try:
                save_figure(fig, plots_dir, filename)
            finally:
                plt.close(fig)

    if len(analysis_results) > 1:
        comp = plot_comparison_tps(analysis_results)
        try:
            save_figure(comp, plots_dir, "comparison_tps")
        finally:
            plt.close(comp)


__all__ = [
    "plot_tps_over_time",
    "plot_errors_over_time",
    "plot_response_times_by_api",
    "plot_error_rate_by_api",
    "plot_comparison_tps",
    "save_figure",
    "create_and_save_graphs",
]
