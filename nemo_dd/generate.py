"""Run a full Data Designer generation job and download the results."""

import argparse

from nemo_dd.client import get_sdk
from nemo_dd.config import build_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Data Designer dataset")
    parser.add_argument(
        "--num-records",
        type=int,
        default=30,
        help="Number of records to generate (default: 30)",
    )
    args = parser.parse_args()

    sdk = get_sdk()
    config_builder = build_config()

    data_designer = sdk.data_designer
    job = data_designer.create(config_builder, num_records=args.num_records)
    job.wait_until_done()

    results = job.download_artifacts()
    dataset = results.load_dataset()
    analysis = results.load_analysis()

    print(dataset.head())
    analysis.to_report()


if __name__ == "__main__":
    main()
