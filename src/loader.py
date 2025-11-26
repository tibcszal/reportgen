import pandas as pd
from os import path, listdir
import json
from typing import Any, Dict
from config_store import load_config


def load(
    requests_dir: str, generator_type: str, config_path: str
) -> dict[str, pd.DataFrame]:
    load_config_file(config_path)
    dfs = load_dfs_per_suite_flat(requests_dir, generator_type)
    return dfs


def load_config_file(config_path: str) -> dict[str, Any] | None:
    return load_config(config_path)


def load_dfs_per_suite_flat(
    requests_dir: str, generator_type: str
) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}

    for entry in sorted(listdir(requests_dir)):
        full_path = path.join(requests_dir, entry)
        if path.isfile(full_path) and entry.endswith(".csv"):
            testname = entry[:-4]
            key = f"__root__.{testname}"
            df = pd.read_csv(full_path)
            if generator_type == "k6":
                df = normalize_k6(df)
            results[key] = df
            resource_df = load_resource_df_if_exists(requests_dir, testname)
            if resource_df is not None:
                results[f"{key}_resources"] = resource_df

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
            resource_df = load_resource_df_if_exists(suite_path, testname)
            if resource_df is not None:
                results[f"{suite_name}.{testname}_resources"] = resource_df

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
            resource_df = load_resource_df_if_exists(requests_dir, testname)
            if resource_df is not None:
                root_suite[f"{testname}_resources"] = resource_df
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
            resource_df = load_resource_df_if_exists(suite_path, testname)
            if resource_df is not None:
                suite_tests[f"{testname}_resources"] = resource_df
        if suite_tests:
            grouped[entry] = suite_tests
    return grouped


def load_resource_df_if_exists(base_dir: str, testname: str) -> pd.DataFrame | None:
    """Return a flattened pod metrics dataframe if the resource file exists."""
    resource_path = path.join(base_dir, f"{testname}_resources.json")
    if not path.isfile(resource_path):
        return None
    return load_resources_json(resource_path)


def load_resources_json(resource_path: str) -> pd.DataFrame:
    with open(resource_path, "r", encoding="UTF-8") as f:
        snapshots = json.load(f)

    rows = []
    for snapshot in snapshots or []:
        timestamp = snapshot.get("timestamp")
        for pod in snapshot.get("pods", []):
            metadata = pod.get("metadata", {})
            podname = metadata.get("name")
            namespace = metadata.get("namespace")
            for container in pod.get("containers", []):
                usage = container.get("usage", {})
                rows.append(
                    {
                        "timestamp": timestamp,
                        "podname": podname,
                        "namespace": namespace,
                        "container": container.get("name"),
                        "cpu": usage.get("cpu"),
                        "memory": usage.get("memory"),
                    }
                )

    columns = ["timestamp", "podname", "namespace", "container", "cpu", "memory"]
    return pd.DataFrame(rows, columns=columns)


def normalize_k6(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["metric_name"] == "http_req_duration"].copy()
    df["label"] = f"{df['method']} {df['url']}"
    df["timeStamp"] = df["timestamp"] * 1000
    df["elapsed"] = df["metric_value"]
    df["responseCode"] = df["status"]
    df["success"] = df["status"] < 400
    return df[["label", "timeStamp", "elapsed", "success", "responseCode"]]
