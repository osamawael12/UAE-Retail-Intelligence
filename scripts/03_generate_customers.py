"""
Generate synthetic customers and customer simulation profiles.

Required existing datasets:
- core_emirates.csv
- core_sales_channels.csv
- product_categories.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.customer_generator import (
    generate_customer_datasets,
)


REQUIRED_FILES = {
    "emirates": "core_emirates.csv",
    "sales_channels": (
        "core_sales_channels.csv"
    ),
    "categories": (
        "product_categories.csv"
    ),
}


OUTPUT_FILES = {
    "customers": (
        "customer_customers.csv"
    ),
    "customer_segment_history": (
        "customer_segment_history.csv"
    ),
    "customer_simulation_profiles": (
        "customer_simulation_profiles.csv"
    ),
}


def load_required_file(
    file_name: str,
) -> pd.DataFrame:
    path = (
        CONFIG.output_directory
        / file_name
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: "
            f"{path}"
        )

    return pd.read_csv(path)


def save_dataframe(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    dataframe.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )


def main() -> None:
    print("=" * 70)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 03 - CUSTOMER DATA GENERATION"
    )
    print("=" * 70)

    validate_generation_config()
    ensure_generation_directories()

    emirates = load_required_file(
        REQUIRED_FILES["emirates"]
    )

    sales_channels = load_required_file(
        REQUIRED_FILES[
            "sales_channels"
        ]
    )

    categories = load_required_file(
        REQUIRED_FILES["categories"]
    )

    datasets = (
        generate_customer_datasets(
            emirates=emirates,
            sales_channels=(
                sales_channels
            ),
            categories=categories,
        )
    )

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():

        file_name = OUTPUT_FILES[
            dataset_name
        ]

        output_path = (
            CONFIG.output_directory
            / file_name
        )

        save_dataframe(
            dataframe=dataframe,
            path=output_path,
        )

        print(
            f"{dataset_name:<32}"
            f"{len(dataframe):>8,} rows"
            f"  -> {file_name}"
        )

    print("-" * 70)
    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()