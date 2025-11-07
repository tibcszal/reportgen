import pandas as pd
from os import path, listdir
import json
from typing import Any


def load(
    requests_dir: str, generator_type: str, config_path: str
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    config = load_config_file(config_path)
    dfs = load_dfs(requests_dir, generator_type)
    return (dfs, config)


def load_config_file(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="UTF-8") as f:
        config_dict: dict[str, Any] = json.load(f)
    return config_dict


def load_dfs(requests_dir: str, generator_type: str) -> dict[str, pd.DataFrame]:
    dfs: dict[str, pd.DataFrame] = {}
    for filename in listdir(requests_dir):
        if not filename.endswith(".csv"):
            continue
        testname = filename[:-4]
        file_path = path.join(requests_dir, filename)
        dfs[testname] = pd.read_csv(file_path)
        if generator_type == "k6":
            dfs[testname] = normalize_k6(dfs[testname])

    return dfs


def normalize_k6(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["metric_name"] == "http_req_duration"].copy()
    df["label"] = df["method"] + " " + df["url"]
    df["timeStamp"] = df["timestamp"] * 1000
    df["elapsed"] = df["metric_value"]
    df["responseCode"] = df["status"]
    df["success"] = df["status"] < 400
    return df[["label", "timeStamp", "elapsed", "success", "responseCode"]]
