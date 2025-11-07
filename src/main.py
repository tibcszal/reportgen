import pandas as pd
from typing import Any
from cli import parse_args
from loader import load
from analyzer import analyze_data
from reporter import generate_excel_report


def main():

    args = parse_args()

    dfs_raw, config = load(args.request_results_dir, args.generator, args.config)

    analysis_results: list[dict[str, Any]] = [
        analyze_data(test_name, df, config) for test_name, df in dfs_raw.items()
    ]

    generate_excel_report(analysis_results, args.output)


if __name__ == "__main__":
    main()
