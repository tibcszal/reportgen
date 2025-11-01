from typing import Optional
import openpyxl as px
import pandas as pd
import sys


def main():
    workbook = px.Workbook()

    # Read data from CSV file
    df_raw: Optional[pd.DataFrame] = read_data()
    if df_raw is None:
        print("Error: failed to read CSV data.")
        sys.exit(1)

    dfs_sorted_by_apis: dict[str, pd.DataFrame] = sort_by_apis(df_raw)

    # egyelore csak legyenek meg ezek az adatok a jmeterbol.
    # szakaszonkent (mp) hany tranzakcio tortent, szakaszonkent mennyi error volt
    # overall minimum maximum valaszido, ugyanez masodpercenkent, vegen atlagolni

    transaction_count_per_api: dict[str, int] = get_transaction_count_per_api(
        dfs_sorted_by_apis
    )

    error_count_per_api: dict[str, int] = get_error_count_per_api(dfs_sorted_by_apis)

    transaction_count: int = sum(transaction_count_per_api.values())
    error_count: int = sum(error_count_per_api.values())

    test_duration_in_seconds: int = get_test_duration_in_seconds(df_raw)

    dfs_by_seconds: dict[int, pd.DataFrame] = get_dfs_by_seconds(df_raw)

    error_count_per_second: dict[int, int] = get_get_error_count_per_second(
        dfs_by_seconds
    )

    print(df_raw.dtypes)

    print(transaction_count_per_api)
    print(transaction_count)
    print(error_count_per_api)
    print(error_count)
    print(test_duration_in_seconds)
    print(error_count_per_second)

    for second, df in dfs_by_seconds.items():
        print(f"Second: {second}, Transactions: {len(df)}")

    print(len(dfs_by_seconds.keys()))

    workbook.save("sample.xlsx")


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


def read_data() -> Optional[pd.DataFrame]:
    path = sys.argv[1]
    return pd.read_csv(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <absolute_path_to_csv>")
        sys.exit(1)
    main()
