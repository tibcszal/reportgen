import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="API performance report generator")
    parser.add_argument("-g", "--generator", choices=["jmeter", "k6"], required=True)
    parser.add_argument("-c", "--config", required=False, default="./config.json")
    parser.add_argument("-req", "--request_results_dir", required=True)
    parser.add_argument("-res", "--resource_usage_dir", required=False)
    parser.add_argument("-o", "--output", required=True)
    return parser.parse_args()
