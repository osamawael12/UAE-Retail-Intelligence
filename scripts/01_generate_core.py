"""
Generate and save all core/reference synthetic datasets.

No SQL Server writes are performed by this script.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.core_generator import (
    generate_core_datasets,
)


FILE_MAPPING = {
    "emirates": "core_emirates.csv",
    "cities": "core_cities.csv",
    "stores": "core_stores.csv",
    "date_dimension": "core_date_dimension.csv",
    "sales_channels": "core_sales_channels.csv",
    "payment_methods": "core_payment_methods.csv",
}


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
    print("=" * 65)
    print("UAE Retail Intelligence Platform")
    print("STEP 01 - CORE DATA GENERATION")
    print("=" * 65)

    validate_generation_config()
    ensure_generation_directories()

    datasets = generate_core_datasets()

    for dataset_name, dataframe in datasets.items():
        file_name = FILE_MAPPING[dataset_name]

        output_path = (
            CONFIG.output_directory
            / file_name
        )

        save_dataframe(
            dataframe=dataframe,
            path=output_path,
        )

        print(
            f"{dataset_name:<20}"
            f"{len(dataframe):>8,} rows"
            f"  -> {file_name}"
        )

    print("-" * 65)
    print(
        f"Output directory: "
        f"{CONFIG.output_directory}"
    )
    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 65)


if __name__ == "__main__":
    main()