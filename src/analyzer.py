import pandas as pd
from typing import Any


def analyze_data(
    test_name: str, df_raw: pd.DataFrame, config: dict[str, Any]
) -> dict[str, Any]:
    dfs_sorted_by_apis: dict[str, pd.DataFrame] = sort_by_apis(df_raw)

    transaction_count_per_api: dict[str, int] = get_transaction_count_per_api(
        dfs_sorted_by_apis
    )

    error_count_per_api: dict[str, int] = get_error_count_per_api(dfs_sorted_by_apis)

    overall_transaction_count: int = sum(transaction_count_per_api.values())
    overall_error_count: int = sum(error_count_per_api.values())

    test_duration_in_seconds: int = get_test_duration_in_seconds(df_raw)

    dfs_by_seconds: dict[int, pd.DataFrame] = get_dfs_by_seconds(df_raw)

    tps_by_second: dict[int, float] = get_tps_by_second(dfs_by_seconds)

    error_count_per_second: dict[int, int] = get_get_error_count_per_second(
        dfs_by_seconds
    )

    overall_maximum_response_time: int = df_raw["elapsed"].max()
    overall_minimum_response_time: int = df_raw["elapsed"].min()

    overall_avg_response_time: float = df_raw["elapsed"].mean()

    maximum_response_time_per_api: dict[str, int] = {
        api: df["elapsed"].max() for api, df in dfs_sorted_by_apis.items()
    }

    minimum_response_time_per_api: dict[str, int] = {
        api: df["elapsed"].min() for api, df in dfs_sorted_by_apis.items()
    }

    average_response_time_per_api: dict[str, float] = {
        api: df["elapsed"].mean() for api, df in dfs_sorted_by_apis.items()
    }

    verdict: str = evaluate_results(
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
        "overall_maximum_response_time": overall_maximum_response_time,
        "overall_minimum_response_time": overall_minimum_response_time,
        "overall_avg_response_time": overall_avg_response_time,
        "maximum_response_time_per_api": maximum_response_time_per_api,
        "minimum_response_time_per_api": minimum_response_time_per_api,
        "average_response_time_per_api": average_response_time_per_api,
        "verdict": verdict,
    }


def evaluate_results(
    overall_error_count: int,
    overall_transaction_count: int,
    tps_by_second: dict[int, float],
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
    dfs_by_seconds: dict[int, pd.DataFrame],
) -> dict[int, float]:
    results: dict[int, float] = {}
    for second, df in dfs_by_seconds.items():
        results[second] = len(df) / 1.0
    return results


def get_dfs_by_seconds(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    results: dict[int, pd.DataFrame] = {}
    for second in range(
        df["timeStamp"].min() // 1000, df["timeStamp"].max() // 1000 + 1
    ):
        results[second] = df[
            (df["timeStamp"] >= second * 1000) & (df["timeStamp"] < (second + 1) * 1000)
        ]
    return results


def get_test_duration_in_seconds(df_raw: pd.DataFrame) -> int:
    return df_raw["timeStamp"].max() // 1000 - df_raw["timeStamp"].min() // 1000 + 1


def get_get_error_count_per_second(
    dfs_by_seconds: dict[int, pd.DataFrame],
) -> dict[int, int]:
    results: dict[int, int] = {}
    for second, df in dfs_by_seconds.items():
        results[second] = get_error_count_from_df(df)
    return results


def get_error_count_per_api(
    dfs_sorted_by_api: dict[str, pd.DataFrame],
) -> dict[str, int]:
    results: dict[str, int] = {}
    for api, df in dfs_sorted_by_api.items():
        results[api] = get_error_count_from_df(df)
    return results


def get_error_count_from_df(df: pd.DataFrame) -> int:
    return len(df[~df["success"]])


def get_transaction_count_per_api(
    dfs_sorted_by_api: dict[str, pd.DataFrame],
) -> dict[str, int]:
    results: dict[str, int] = {}
    for api, df in dfs_sorted_by_api.items():
        results[api] = len(df)
    return results


def sort_by_apis(df_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    results_dict: dict[str, pd.DataFrame] = {}
    for api in df_raw["label"].unique():
        results_dict[api] = df_raw[df_raw["label"] == api]
    return results_dict
