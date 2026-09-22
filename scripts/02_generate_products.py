"""
Generate and save product master datasets.

The script performs no SQL Server writes.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.product_generator import (
    generate_product_datasets,
)


FILE_MAPPING = {
    "categories": "product_categories.csv",
    "subcategories": "product_subcategories.csv",
    "brands": "product_brands.csv",
    "suppliers": "product_suppliers_master.csv",
    "products": "product_products.csv",
    "product_suppliers": (
        "product_product_suppliers.csv"
    ),
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
    print("=" * 70)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 02 - PRODUCT DATA GENERATION"
    )
    print("=" * 70)

    validate_generation_config()
    ensure_generation_directories()

    datasets = (
        generate_product_datasets()
    )

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():

        file_name = FILE_MAPPING[
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
            f"{dataset_name:<22}"
            f"{len(dataframe):>8,} rows"
            f"  -> {file_name}"
        )

    print("-" * 70)
    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()