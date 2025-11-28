from __future__ import annotations

from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import math
import os
import html
import re
from .config_store import get_config_value
import base64
from io import BytesIO


def _series_from_second_map(
    data_map: Dict[Any, Any]
) -> tuple[list[int], list[float]]:
    if not data_map:
        return [], []
    series: list[tuple[int, float]] = []
    for k, v in data_map.items():
        try:
            sec = int(k)
            val = float(v)
        except (TypeError, ValueError):
            continue
        series.append((sec, val))
    if not series:
        return [], []
    series.sort(key=lambda x: x[0])
    seconds = [sec for sec, _ in series]
    values = [val for _, val in series]
    return seconds, values


def plot_tps_over_time(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    if not is_transaction_result(result):
        return _empty_fig("No transaction data")
    tps_by_second: Dict[str, float] = result.get("transaction_count_per_second", {})
    duration = int(result.get("test_duration_in_seconds", len(tps_by_second)))
    if duration <= 0:
        return _empty_fig("No duration")
    seconds, tps_values = _series_from_second_map(tps_by_second)
    fig, ax = plt.subplots(figsize=(8, 4))
    marker_style = "o" if duration <= 120 else None
    ax.plot(seconds, tps_values, marker=marker_style, linewidth=1.4)
    if duration > 0 and seconds:
        ax.set_xlim(1, max(seconds))
    ax.set_ylim(0, get_config_value("target_tps", 100))
    ax.set_xlabel("Second")
    ax.set_ylabel("Transactions")
    ax.set_title(title or f"TPS Over Time: {result.get('test_name', 'unknown')}")
    ax.grid(True, linestyle="--", alpha=0.4)
    return fig


def plot_errors_over_time(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    if not is_transaction_result(result):
        return _empty_fig("No error data")
    err_map: Dict[int, int] = result.get("error_count_per_second", {})
    duration = int(result.get("test_duration_in_seconds", len(err_map)))
    if duration <= 0:
        return _empty_fig("No duration")
    seconds, err_values = _series_from_second_map(err_map)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(seconds, err_values, color="#d9534f")
    if duration > 0 and seconds:
        ax.set_xlim(1, max(seconds))
    ax.set_xlabel("Second")
    ax.set_ylabel("Errors")
    ax.set_title(title or f"Errors Over Time: {result.get('test_name', 'unknown')}")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    return fig


def plot_response_times_by_api(
    result: Dict[str, Any], *, title: Optional[str] = None
) -> Figure:
    if not is_transaction_result(result):
        return _empty_fig("No response time data")
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
    if not is_transaction_result(result):
        return _empty_fig("No error rate data")
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
    ax.set_xticks(list(apis))
    ax.set_xticklabels(apis, rotation=45, ha="right")
    ax.set_ylim(0, max(rates) * 1.15 if rates else 1)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    return fig


def plot_comparison_tps(
    results: List[Dict[str, Any]], *, title: str = "TPS Comparison"
) -> Figure:
    if not results:
        return _empty_fig("No results provided")
    results = [r for r in results if is_transaction_result(r)]
    if not results:
        return _empty_fig("No transaction results provided")
    max_duration = max(int(r.get("test_duration_in_seconds", 0)) for r in results)
    fig, ax = plt.subplots(figsize=(9, 5))
    for r in results:
        tps_map: Dict[int, float] = r.get("transaction_count_per_second", {})
        seconds, tps_values = _series_from_second_map(tps_map)
        marker_style = "o" if max_duration <= 120 else None
        ax.plot(
            seconds,
            tps_values,
            marker=marker_style,
            linewidth=1.1,
            label=r.get("test_name", "unknown"),
        )
    ax.set_xlim(1, max_duration)
    ax.set_ylim(0, get_config_value("target_tps", 100))
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
    html_output = os.path.join(plots_dir, "dashboard.html")
    graphs_by_suite: dict[str, dict[str, list[dict[str, str]]]] = {}

    resource_results_by_base: Dict[str, Dict[str, Any]] = {
        _base_test_name(r.get("test_name", "unknown")): r
        for r in analysis_results
        if is_resource_result(r)
    }
    tx_results = [r for r in analysis_results if is_transaction_result(r)]
    for result in tx_results:
        test_name = result.get("test_name", "unknown")
        base_name = _base_test_name(test_name)
        if "." in test_name:
            suite, test = test_name.split(".", 1)
        else:
            suite, test = "__root__", test_name
        resource_result = resource_results_by_base.get(base_name)
        figures: list[tuple[Figure, str]] = [
            (plot_tps_over_time(result), f"TPS Over Time"),
            (plot_errors_over_time(result), f"Errors Over Time"),
            (plot_response_times_by_api(result), f"Response Times by API"),
            (plot_error_rate_by_api(result), f"Error Rate by API"),
        ]
        if resource_result:
            figures.append(
                (
                    plot_tps_vs_resource_usage(
                        result,
                        resource_result,
                        title=f"TPS vs Resources",
                    ),
                    f"TPS vs Resources",
                )
            )
            figures.append(
                (plot_tps_vs_cpu(result, resource_result), f"TPS vs CPU")
            )
            figures.append(
                (
                    plot_tps_vs_memory(result, resource_result),
                    f"TPS vs Memory",
                )
            )
            figures.append(
                (
                    plot_errors_vs_resources(result, resource_result),
                    f"Errors vs Resources",
                )
            )
            figures.append(
                (plot_errors_vs_cpu(result, resource_result), f"Errors vs CPU")
            )
            figures.append(
                (
                    plot_errors_vs_memory(result, resource_result),
                    f"Errors vs Memory",
                )
            )
        for fig, title in figures:
            _add_graph(graphs_by_suite, suite, test, title, fig)

    if len(tx_results) > 1:
        comp = plot_comparison_tps(tx_results)
        _add_graph(graphs_by_suite, "__overall__", "all_tests", "TPS Comparison", comp)

    _render_dashboard(graphs_by_suite, html_output)


__all__ = [
    "plot_tps_over_time",
    "plot_errors_over_time",
    "plot_response_times_by_api",
    "plot_error_rate_by_api",
    "plot_tps_vs_resource_usage",
    "plot_tps_vs_cpu",
    "plot_tps_vs_memory",
    "plot_errors_vs_resources",
    "plot_errors_vs_cpu",
    "plot_errors_vs_memory",
    "plot_comparison_tps",
    "save_figure",
    "create_and_save_graphs",
]


def is_transaction_result(result: Dict[str, Any]) -> bool:
    return "transaction_count_per_second" in result or "overall_transaction_count" in result


def is_resource_result(result: Dict[str, Any]) -> bool:
    return "cpu_avg_per_pod" in result or ("overall" in result and "overall_avg_cpu_mcores" in result["overall"])


def _empty_fig(message: str) -> Figure:
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.set_axis_off()
    return fig


def _series_from_time_map(
    time_map: Dict[Any, float], sampling_interval: float | int = 1
) -> tuple[list[int], list[float]]:
    if not time_map:
        return [], []
    series: list[tuple[float, float]] = []
    for k, v in time_map.items():
        try:
            t = float(k)
            value = float(v)
        except (TypeError, ValueError):
            continue
        series.append((t, value))
    if not series:
        seconds = list(range(1, len(time_map) + 1))
        return seconds, list(time_map.values())
    series.sort(key=lambda x: x[0])
    times = [t for t, _ in series]
    if max(times) > 1e10:
        times = [t / 1000.0 for t in times]
    start = min(times)
    norm_times = [int(round(t - start + 1)) for t in times]
    try:
        interval = float(sampling_interval)
    except (TypeError, ValueError):
        interval = 1.0
    interval = interval if interval > 0 else 1.0
    scaled_times = [int(round(t * interval)) for t in norm_times]
    values = [v for _, v in series]
    return scaled_times, values


def _has_valid_data(values: list[float]) -> bool:
    return any(isinstance(v, (int, float)) and not math.isnan(v) for v in values)


def _figure_to_base64(fig: Figure, *, fmt: str = "png") -> str:
    buf = BytesIO()
    fig.savefig(buf, format=fmt, bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/{fmt};base64,{data}"


def _add_graph(
    graphs: dict[str, dict[str, list[dict[str, str]]]],
    suite: str,
    test: str,
    title: str,
    fig: Figure,
) -> None:
    graphs.setdefault(suite, {}).setdefault(test, []).append(
        {"title": title, "src": _figure_to_base64(fig)}
    )


def _safe_id(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", text)


def _render_dashboard(graphs_by_suite: dict[str, dict[str, list[dict[str, str]]]], output_path: str) -> None:
    overall = graphs_by_suite.get("__overall__", {})
    overall_graphs = []
    if overall:
        # Expect a single bucket like all_tests; flatten graphs
        for charts in overall.values():
            overall_graphs.extend(charts)

    suites = sorted(k for k in graphs_by_suite.keys() if k != "__overall__")

    overall_section = ""
    if overall_graphs:
        cards = "".join(
            f'''
            <div class="card">
                <div class="card-title">{html.escape(chart["title"])}</div>
                <img src="{chart["src"]}" alt="{html.escape(chart["title"])}" loading="lazy" />
            </div>
            '''
            for chart in overall_graphs
        )
        overall_section = f"""
        <section class="suite-section">
            <h2>Overall</h2>
            <div class="card-grid">{cards}</div>
        </section>
        """

    suite_sections: list[str] = []
    for suite in suites:
        tests = graphs_by_suite[suite]
        test_details: list[str] = []
        for test_name, charts in sorted(tests.items()):
            cards = "".join(
                f'''
                <div class="card">
                    <div class="card-title">{html.escape(chart["title"])}</div>
                    <img src="{chart["src"]}" alt="{html.escape(chart["title"])}" loading="lazy" />
                </div>
                '''
                for chart in charts
            )
            test_details.append(
                f'''
                <details class="test-details">
                    <summary>{html.escape(test_name)}</summary>
                    <div class="card-grid">
                        {cards}
                    </div>
                </details>
                '''
            )
        suite_sections.append(
            f'''
            <details class="suite-details">
                <summary>{html.escape(suite)}</summary>
                <div class="test-list">
                    {''.join(test_details)}
                </div>
            </details>
            '''
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Performance Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8f9fa; color: #222; }}
    header {{ background: #343a40; color: white; padding: 12px 16px; position: sticky; top: 0; z-index: 10; }}
    h1 {{ margin: 0; font-size: 20px; }}
    main {{ padding: 16px; }}
    .suite-section {{ margin-bottom: 24px; }}
    .card-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
    .card {{ background: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }}
    .card-title {{ font-weight: 600; margin-bottom: 8px; font-size: 14px; }}
    img {{ width: 100%; height: auto; display: block; border-radius: 4px; }}
    .suite-details, .test-details {{ margin-bottom: 10px; border: 1px solid #dee2e6; border-radius: 6px; background: white; }}
    .suite-details > summary, .test-details > summary {{ cursor: pointer; padding: 10px 12px; font-weight: 600; list-style: none; }}
    .suite-details > summary::-webkit-details-marker, .test-details > summary::-webkit-details-marker {{ display: none; }}
    .suite-details > summary::before, .test-details > summary::before {{ content: "▶"; display: inline-block; margin-right: 8px; transition: transform 0.2s ease; }}
    .suite-details[open] > summary::before, .test-details[open] > summary::before {{ transform: rotate(90deg); }}
    .test-list {{ padding: 0 12px 12px 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>Performance Dashboard</h1>
  </header>
  <main>
    {overall_section}
    <section class="suite-section">
        <h2>Suites</h2>
        <div class="suite-list">
            {''.join(suite_sections)}
        </div>
    </section>
  </main>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)


def _plot_metric_with_resources(
    metric_seconds: list[int],
    metric_values: list[float],
    cpu_seconds: list[int],
    cpu_values: list[float],
    mem_seconds: list[int],
    mem_values: list[float],
    *,
    metric_label: str,
    title: str,
    metric_color: str = "#007bff",
) -> Figure:
    has_cpu = _has_valid_data(cpu_values)
    has_mem = _has_valid_data(mem_values)

    if not metric_values or (not has_cpu and not has_mem):
        return _empty_fig("No overlapping data")

    max_time = max(
        [metric_seconds[-1] if metric_seconds else 0]
        + ([max(cpu_seconds)] if has_cpu and cpu_seconds else [])
        + ([max(mem_seconds)] if has_mem and mem_seconds else [])
    )

    fig, ax1 = plt.subplots(figsize=(9, 5))
    metric_line = ax1.plot(
        metric_seconds,
        metric_values,
        label=metric_label,
        color=metric_color,
        linewidth=1.3,
    )
    ax1.set_xlabel("Second")
    ax1.set_ylabel(metric_label)
    ax1.set_xlim(1, max_time)
    ax1.grid(True, linestyle="--", alpha=0.35)

    handles = list(metric_line)
    if has_cpu or has_mem:
        ax2 = ax1.twinx()
        if has_cpu:
            cpu_line = ax2.plot(
                cpu_seconds,
                cpu_values,
                label="CPU (mcores)",
                color="#f0ad4e",
                linestyle="--",
                linewidth=1.1,
            )
            handles.extend(cpu_line)
        if has_mem:
            mem_line = ax2.plot(
                mem_seconds,
                mem_values,
                label="Memory (MiB)",
                color="#5cb85c",
                linestyle=":",
                linewidth=1.1,
            )
            handles.extend(mem_line)
        ax2.set_ylabel("CPU / Memory")

    ax1.set_title(title)
    ax1.legend(handles=handles, loc="upper right")
    fig.tight_layout()
    return fig


def _bytes_to_mib(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value) / (1024**2)
    except (TypeError, ValueError):
        return None


def _base_test_name(test_name: str) -> str:
    return test_name[:-10] if test_name.endswith("_resources") else test_name


def plot_tps_vs_resource_usage(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
    *,
    title: Optional[str] = None,
) -> Figure:
    if not (is_transaction_result(result) and is_resource_result(resource_result)):
        return _empty_fig("No matching transaction/resource data")

    tps_map: Dict[str, float] = result.get("transaction_count_per_second", {})
    cpu_map: Dict[str, float] = resource_result.get("cpu_max_over_time", {}) or resource_result.get("cpu_avg_over_time", {})
    mem_map_raw: Dict[str, float] = resource_result.get("memory_max_over_time", {}) or resource_result.get("memory_avg_over_time", {})
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)

    tps_seconds, tps_values = _series_from_second_map(tps_map)
    cpu_seconds, cpu_values = _series_from_time_map(cpu_map, sampling_interval=sampling_interval)
    mem_seconds, mem_bytes = _series_from_time_map(mem_map_raw, sampling_interval=sampling_interval)
    mem_values: list[float] = []
    for val in mem_bytes:
        converted = _bytes_to_mib(val)
        mem_values.append(converted if converted is not None else math.nan)
    has_cpu = _has_valid_data(cpu_values)
    has_mem = _has_valid_data(mem_values)

    if not tps_values or (not has_cpu and not has_mem):
        return _empty_fig("No overlapping TPS/resource data")

    max_time = max(
        [tps_seconds[-1] if tps_seconds else 0]
        + ([max(cpu_seconds)] if cpu_seconds else [])
        + ([max(mem_seconds)] if mem_seconds else [])
    )

    fig, ax1 = plt.subplots(figsize=(9, 5))
    tps_line = ax1.plot(
        tps_seconds, tps_values, label="TPS", color="#007bff", linewidth=1.3
    )
    ax1.set_xlabel("Second")
    ax1.set_ylabel("Transactions per second")
    ax1.set_xlim(1, float(max_time))
    ax1.set_ylim(0, get_config_value("target_tps", 100))
    ax1.grid(True, linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()
    handles = list(tps_line)

    if has_cpu:
        cpu_line = ax2.plot(
            cpu_seconds,
            cpu_values,
            label="CPU (mcores)",
            color="#f0ad4e",
            linestyle="--",
            linewidth=1.1,
        )
        handles.extend(cpu_line)
    if has_mem:
        mem_line = ax2.plot(
            mem_seconds,
            mem_values,
            label="Memory (MiB)",
            color="#5cb85c",
            linestyle=":",
            linewidth=1.1,
        )
        handles.extend(mem_line)
    if has_cpu or has_mem:
        ax2.set_ylabel("CPU / Memory")

    ax1.set_title(
        title
        or f"TPS vs Resources Over Time: {_base_test_name(result.get('test_name', 'unknown'))}"
    )
    ax1.legend(handles=handles, loc="upper right")
    fig.tight_layout()
    return fig


def plot_tps_vs_cpu(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
) -> Figure:
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)
    tps_map: Dict[str, float] = result.get("transaction_count_per_second", {})
    cpu_map: Dict[str, float] = resource_result.get("cpu_max_over_time", {}) or resource_result.get("cpu_avg_over_time", {})

    tps_seconds, tps_values = _series_from_second_map(tps_map)
    cpu_seconds, cpu_values = _series_from_time_map(
        cpu_map, sampling_interval=sampling_interval
    )

    return _plot_metric_with_resources(
        tps_seconds,
        tps_values,
        cpu_seconds,
        cpu_values,
        [],
        [],
        metric_label="TPS",
        title=f"TPS vs CPU: {_base_test_name(result.get('test_name', 'unknown'))}",
    )


def plot_tps_vs_memory(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
) -> Figure:
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)
    tps_map: Dict[str, float] = result.get("transaction_count_per_second", {})
    mem_map_raw: Dict[str, float] = resource_result.get("memory_max_over_time", {}) or resource_result.get("memory_avg_over_time", {})

    tps_seconds, tps_values = _series_from_second_map(tps_map)
    mem_seconds, mem_bytes = _series_from_time_map(
        mem_map_raw, sampling_interval=sampling_interval
    )
    mem_values: list[float] = []
    for val in mem_bytes:
        converted = _bytes_to_mib(val)
        mem_values.append(converted if converted is not None else math.nan)

    return _plot_metric_with_resources(
        tps_seconds,
        tps_values,
        [],
        [],
        mem_seconds,
        mem_values,
        metric_label="TPS",
        title=f"TPS vs Memory: {_base_test_name(result.get('test_name', 'unknown'))}",
    )


def plot_errors_vs_resources(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
) -> Figure:
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)
    err_map: Dict[int, int] = result.get("error_count_per_second", {})
    cpu_map: Dict[str, float] = resource_result.get("cpu_max_over_time", {}) or resource_result.get("cpu_avg_over_time", {})
    mem_map_raw: Dict[str, float] = resource_result.get("memory_max_over_time", {}) or resource_result.get("memory_avg_over_time", {})

    err_seconds, err_values = _series_from_second_map(err_map)
    cpu_seconds, cpu_values = _series_from_time_map(
        cpu_map, sampling_interval=sampling_interval
    )
    mem_seconds, mem_bytes = _series_from_time_map(
        mem_map_raw, sampling_interval=sampling_interval
    )
    mem_values: list[float] = []
    for val in mem_bytes:
        converted = _bytes_to_mib(val)
        mem_values.append(converted if converted is not None else math.nan)

    return _plot_metric_with_resources(
        err_seconds,
        err_values,
        cpu_seconds,
        cpu_values,
        mem_seconds,
        mem_values,
        metric_label="Errors",
        metric_color="#d9534f",
        title=f"Errors vs Resources: {_base_test_name(result.get('test_name', 'unknown'))}",
    )


def plot_errors_vs_cpu(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
) -> Figure:
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)
    err_map: Dict[int, int] = result.get("error_count_per_second", {})
    cpu_map: Dict[str, float] = resource_result.get("cpu_max_over_time", {}) or resource_result.get("cpu_avg_over_time", {})

    err_seconds, err_values = _series_from_second_map(err_map)
    cpu_seconds, cpu_values = _series_from_time_map(
        cpu_map, sampling_interval=sampling_interval
    )

    return _plot_metric_with_resources(
        err_seconds,
        err_values,
        cpu_seconds,
        cpu_values,
        [],
        [],
        metric_label="Errors",
        metric_color="#d9534f",
        title=f"Errors vs CPU: {_base_test_name(result.get('test_name', 'unknown'))}",
    )


def plot_errors_vs_memory(
    result: Dict[str, Any],
    resource_result: Dict[str, Any],
) -> Figure:
    sampling_interval = get_config_value("resource_sampling_rate_in_seconds", 1)
    err_map: Dict[int, int] = result.get("error_count_per_second", {})
    mem_map_raw: Dict[str, float] = resource_result.get("memory_max_over_time", {}) or resource_result.get("memory_avg_over_time", {})

    err_seconds, err_values = _series_from_second_map(err_map)
    mem_seconds, mem_bytes = _series_from_time_map(
        mem_map_raw, sampling_interval=sampling_interval
    )
    mem_values: list[float] = []
    for val in mem_bytes:
        converted = _bytes_to_mib(val)
        mem_values.append(converted if converted is not None else math.nan)

    return _plot_metric_with_resources(
        err_seconds,
        err_values,
        [],
        [],
        mem_seconds,
        mem_values,
        metric_label="Errors",
        metric_color="#d9534f",
        title=f"Errors vs Memory: {_base_test_name(result.get('test_name', 'unknown'))}",
    )
