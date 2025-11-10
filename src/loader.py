import pandas as pd
from os import path, listdir
import json
from typing import Any, Dict


def load(
    requests_dir: str, generator_type: str, config_path: str
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    config = load_config_file(config_path)
    dfs = load_dfs_per_suite_flat(requests_dir, generator_type)
    return (dfs, config)


def load_config_file(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="UTF-8") as f:
        config_dict: dict[str, Any] = json.load(f)
    return config_dict


def load_dfs_per_suite_flat(
    requests_dir: str, generator_type: str
) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}

    for entry in sorted(listdir(requests_dir)):
        full_path = path.join(requests_dir, entry)
        if path.isfile(full_path) and entry.endswith(".csv"):
            key = f"__root__.{entry[:-4]}"
            df = pd.read_csv(full_path)
            if generator_type == "k6":
                df = normalize_k6(df)
            results[key] = df

    for entry in sorted(listdir(requests_dir)):
        suite_path = path.join(requests_dir, entry)
        if not path.isdir(suite_path):
            continue
        suite_name = entry
        for filename in sorted(listdir(suite_path)):
            if not filename.endswith(".csv"):
                continue
            testname = filename[:-4]
            file_path = path.join(suite_path, filename)
            df = pd.read_csv(file_path)
            if generator_type == "k6":
                df = normalize_k6(df)
            results[f"{suite_name}.{testname}"] = df

    return results


def load_dfs_grouped(
    requests_dir: str, generator_type: str
) -> dict[str, Dict[str, pd.DataFrame]]:
    grouped: dict[str, Dict[str, pd.DataFrame]] = {}
    root_suite: Dict[str, pd.DataFrame] = {}
    for entry in listdir(requests_dir):
        full_path = path.join(requests_dir, entry)
        if path.isfile(full_path) and entry.endswith(".csv"):
            testname = entry[:-4]
            df = pd.read_csv(full_path)
            if generator_type == "k6":
                df = normalize_k6(df)
            root_suite[testname] = df
    if root_suite:
        grouped["__root__"] = root_suite

    for entry in listdir(requests_dir):
        suite_path = path.join(requests_dir, entry)
        if not path.isdir(suite_path):
            continue
        suite_tests: Dict[str, pd.DataFrame] = {}
        for filename in listdir(suite_path):
            if not filename.endswith(".csv"):
                continue
            testname = filename[:-4]
            file_path = path.join(suite_path, filename)
            df = pd.read_csv(file_path)
            if generator_type == "k6":
                df = normalize_k6(df)
            suite_tests[testname] = df
        if suite_tests:
            grouped[entry] = suite_tests
    return grouped


def normalize_k6(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["metric_name"] == "http_req_duration"].copy()
    df["label"] = df["method"] + " " + df["url"]
    df["timeStamp"] = df["timestamp"] * 1000
    df["elapsed"] = df["metric_value"]
    df["responseCode"] = df["status"]
    df["success"] = df["status"] < 400
    return df[["label", "timeStamp", "elapsed", "success", "responseCode"]]
