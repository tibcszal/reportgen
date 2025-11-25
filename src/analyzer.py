import pandas as pd
from typing import Any, Callable


def analyze_data(
    test_name: str, df_raw: pd.DataFrame, config: dict[str, Any]
) -> dict[str, Any]:
    if is_resource_dataframe(df_raw):
        return analyze_resource_data(test_name, df_raw)
    return analyze_results_data(test_name, df_raw, config)


def is_resource_dataframe(df: pd.DataFrame) -> bool:
    required = {"timestamp", "podname", "namespace", "container", "cpu", "memory"}
    return required.issubset(df.columns)


def analyze_results_data(
    test_name: str, df_raw: pd.DataFrame, config: dict[str, Any]
) -> dict[str, Any]:
    dfs_sorted_by_apis = sort_by(df_raw, "label")

    transaction_count_per_api = get_counts_by_group(dfs_sorted_by_apis, len)
    error_count_per_api = get_counts_by_group(
        dfs_sorted_by_apis, lambda df: get_error_count_from_df(df)
    )

    overall_transaction_count = sum(transaction_count_per_api.values())
    overall_error_count = sum(error_count_per_api.values())

    test_duration_in_seconds = get_test_duration_in_seconds(df_raw)

    dfs_by_seconds = get_dfs_by_seconds(df_raw)
    tps_by_second = get_tps_by_second(dfs_by_seconds)
    error_count_per_second = get_error_count_per_second(dfs_by_seconds)

    response_time_stats = get_response_time_stats(df_raw, dfs_sorted_by_apis)
    verdict = evaluate_results(
        overall_error_count, overall_transaction_count, tps_by_second, config
    )

    return {
        "test_name": test_name,
        "transaction_count_per_api": transaction_count_per_api,
        "error_count_per_api": error_count_per_api,
        "overall_transaction_count": overall_transaction_count,
        "overall_error_count": overall_error_count,
        "test_duration_in_seconds": test_duration_in_seconds,
        "error_count_per_second": error_count_per_second,
        "transaction_count_per_second": tps_by_second,
        "overall_maximum_response_time": response_time_stats["overall_max"],
        "overall_minimum_response_time": response_time_stats["overall_min"],
        "overall_avg_response_time": response_time_stats["overall_avg"],
        "maximum_response_time_per_api": response_time_stats["max_per_group"],
        "minimum_response_time_per_api": response_time_stats["min_per_group"],
        "average_response_time_per_api": response_time_stats["avg_per_group"],
        "verdict": verdict,
    }


def analyze_resource_data(test_name: str, df_raw: pd.DataFrame) -> dict[str, Any]:
    df = add_numeric_resource_columns(df_raw)
    dfs_by_pod = sort_by(df, "podname")

    cpu_avg_per_pod = get_numeric_by_group(dfs_by_pod, "cpu_mcores", "mean")
    cpu_max_per_pod = get_numeric_by_group(dfs_by_pod, "cpu_mcores", "max")
    cpu_min_per_pod = get_numeric_by_group(dfs_by_pod, "cpu_mcores", "min")
    mem_avg_per_pod = get_numeric_by_group(dfs_by_pod, "memory_bytes", "mean")
    mem_max_per_pod = get_numeric_by_group(dfs_by_pod, "memory_bytes", "max")
    mem_min_per_pod = get_numeric_by_group(dfs_by_pod, "memory_bytes", "min")

    overall = {
        "overall_avg_cpu_mcores": df["cpu_mcores"].mean(),
        "overall_max_cpu_mcores": df["cpu_mcores"].max(),
        "overall_avg_memory_bytes": df["memory_bytes"].mean(),
        "overall_max_memory_bytes": df["memory_bytes"].max(),
        "start_timestamp": df["timestamp"].min(),
        "end_timestamp": df["timestamp"].max(),
        "snapshot_count": len(df["timestamp"].unique()),
    }

    return {
        "test_name": test_name,
        "cpu_avg_per_pod": cpu_avg_per_pod,
        "cpu_max_per_pod": cpu_max_per_pod,
        "cpu_min_per_pod": cpu_min_per_pod,
        "memory_avg_per_pod": mem_avg_per_pod,
        "memory_max_per_pod": mem_max_per_pod,
        "memory_min_per_pod": mem_min_per_pod,
        "overall": overall,
    }

def get_numeric_by_group(
    grouped: dict[str, pd.DataFrame], column: str, operation: str
) -> dict[str, float]:
    results: dict[str, float] = {}
    for name, df in grouped.items():
        if operation == "mean":
            results[name] = df[column].mean()
        elif operation == "max":
            results[name] = df[column].max()
        elif operation == "min":
            results[name] = df[column].min()
    return results

def evaluate_results(
    overall_error_count: int,
    overall_transaction_count: int,
    tps_by_second: dict[str, float],
    config: dict[str, Any],
) -> str:
    if (overall_error_count / overall_transaction_count) > config[
        "error_rate_threshold"
    ]:
        return "FAIL"
    for tps in tps_by_second.values():
        if tps < config["tps_threshold"]:
            return "FAIL"
    return "PASS"


def get_tps_by_second(
    dfs_by_seconds: dict[str, pd.DataFrame],
) -> dict[str, float]:
    results: dict[str, float] = {}
    for second, df in dfs_by_seconds.items():
        results[second] = len(df) / 1.0
    return results


def get_dfs_by_seconds(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    for second in range(
        df["timeStamp"].min() // 1000, df["timeStamp"].max() // 1000 + 1
    ):
        results[f"second"] = df[
            (df["timeStamp"] >= second * 1000) & (df["timeStamp"] < (second + 1) * 1000)
        ]
    return results


def get_test_duration_in_seconds(df_raw: pd.DataFrame) -> int:
    return df_raw["timeStamp"].max() // 1000 - df_raw["timeStamp"].min() // 1000 + 1


def get_error_count_per_second(
    dfs_by_seconds: dict[str, pd.DataFrame],
) -> dict[str, int]:
    return get_counts_by_group(dfs_by_seconds, lambda df: get_error_count_from_df(df))


def get_error_count_per_api(
    dfs_sorted_by_api: dict[str, pd.DataFrame],
) -> dict[str, int]:
    return get_counts_by_group(dfs_sorted_by_api, lambda df: get_error_count_from_df(df))


def get_error_count_from_df(df: pd.DataFrame) -> int:
    return len(df[~df["success"]])


def get_transaction_count_per_api(
    dfs_sorted_by_api: dict[str, pd.DataFrame],
) -> dict[str, int]:
    return get_counts_by_group(dfs_sorted_by_api, len)


def sort_by(df_raw: pd.DataFrame, column: str) -> dict[str, pd.DataFrame]:
    results_dict: dict[str, pd.DataFrame] = {}
    for value in df_raw[column].unique():
        results_dict[str(value)] = df_raw[df_raw[column] == value]
    return results_dict


def get_counts_by_group(
    grouped: dict[str, pd.DataFrame], counter: Callable[[pd.DataFrame], int]
) -> dict[str, int]:
    results: dict[str, int] = {}
    for name, df in grouped.items():
        results[name] = counter(df)
    return results


def get_response_time_stats(
    df_raw: pd.DataFrame, dfs_sorted_by_apis: dict[str, pd.DataFrame]
) -> dict[str, Any]:
    return {
        "overall_max": df_raw["elapsed"].max(),
        "overall_min": df_raw["elapsed"].min(),
        "overall_avg": df_raw["elapsed"].mean(),
        "max_per_group": {api: df["elapsed"].max() for api, df in dfs_sorted_by_apis.items()},
        "min_per_group": {api: df["elapsed"].min() for api, df in dfs_sorted_by_apis.items()},
        "avg_per_group": {api: df["elapsed"].mean() for api, df in dfs_sorted_by_apis.items()},
    }


def add_numeric_resource_columns(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["cpu_mcores"] = df["cpu"].apply(parse_cpu_to_mcores)
    df["memory_bytes"] = df["memory"].apply(parse_memory_to_bytes)
    return df


def parse_cpu_to_mcores(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) * 1000
    text = str(value).strip()
    if text.endswith("m"):
        return float(text[:-1])
    try:
        return float(text) * 1000
    except ValueError:
        return 0.0


def parse_memory_to_bytes(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    units = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "Pi": 1024**5,
        "Ei": 1024**6,
        "k": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4,
    }
    for suffix, multiplier in units.items():
        if text.endswith(suffix):
            try:
                return float(text[: -len(suffix)]) * multiplier
            except ValueError:
                return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0
