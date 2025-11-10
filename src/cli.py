import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="API performance report generator")
    parser.add_argument("-g", "--generator", choices=["jmeter", "k6"], required=True)
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        default="/home/tcz/Documents/Uni/Thesis/report_generation_thesis/src/config.json",
    )
    parser.add_argument("-req", "--request_results_dir", required=True)
    parser.add_argument("-res", "--resource_usage_dir", required=False)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument(
        "-p",
        "--plots_dir",
        required=False,
        default="/home/tcz/Documents/Uni/Thesis/plots",
        help="Directory to save generated plot images (default: plots)",
    )
    parser.add_argument("-d", "--dry-run", required=False, action="store_true")
    return parser.parse_args()
