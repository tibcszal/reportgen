from typing import Any
from .cli import parse_args
from .loader import load
from .analyzer import analyze_data
from .reporter import generate_excel_report
from .graphs import create_and_save_graphs
from .config_store import get_config_value, get_storage_config
from .storage import append_verdicts


def main():

    args = parse_args()

    print("Loading results...")
    dfs_raw = load(args.results_dir, args.generator, args.config)

    print("Analyzing results...")
    analysis_results: list[dict[str, Any]] = [
        analyze_data(test_name, df) for test_name, df in dfs_raw.items()
    ]

    storage_config = get_storage_config()
    history: dict[str, dict[str, str]] | None = None
    if storage_config.get("enabled", True):
        print("Saving verdict history...")
        history = append_verdicts(analysis_results)
    else:
        print("Verdict history storage is disabled by config, saving results skipped.")

    graphs_config = get_config_value("graphs", {}) or {}

    if not graphs_config.get("enabled", True):
        print("Plotting is disabled by config, skipping graph generation.")
    else:
        print("Creating and saving graphs...")
        create_and_save_graphs(analysis_results, args.plots_dir, history=history)
    if args.dry_run:
        print("Dry run enabled, skipping report generation.")
        return
    print("Creating and saving excel report...")
    generate_excel_report(analysis_results, args.output)


if __name__ == "__main__":
    main()
