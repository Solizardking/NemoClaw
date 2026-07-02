"""Fast local preview of the Data Designer dataset (no full job run)."""

from nemo_dd.client import get_sdk
from nemo_dd.config import build_config


def main() -> None:
    sdk = get_sdk()
    config_builder = build_config()

    data_designer = sdk.data_designer
    preview = data_designer.preview(config_builder)

    preview.display_sample_record()

    df = preview.dataset
    print(df.head())

    preview.analysis.to_report()


if __name__ == "__main__":
    main()
