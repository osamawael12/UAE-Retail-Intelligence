"""
Generate synthetic retail promotion datasets.

Required inputs:
- product_categories.csv
- product_products.csv
- core_stores.csv

Outputs:
- sales_promotions.csv
- sales_promotion_products.csv
- sales_promotion_categories.csv
- sales_promotion_stores.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.promotion_generator import (
    generate_promotion_datasets,
)


INPUT_FILES = {
    "categories": (
        "product_categories.csv"
    ),
    "products": (
        "product_products.csv"
    ),
    "stores": (
        "core_stores.csv"
    ),
}


OUTPUT_FILES = {
    "promotions": (
        "sales_promotions.csv"
    ),
    "promotion_products": (
        "sales_promotion_products.csv"
    ),
    "promotion_categories": (
        "sales_promotion_categories.csv"
    ),
    "promotion_stores": (
        "sales_promotion_stores.csv"
    ),
}


def load_dataset(
    file_name: str,
) -> pd.DataFrame:
    path = (
        CONFIG.output_directory
        / file_name
    )

    if not path.exists():
        raise FileNotFoundError(
            "Required dataset not found: "
            f"{path}"
        )

    return pd.read_csv(path)


def save_dataset(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )


def main() -> None:
    print("=" * 72)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 05 - PROMOTION DATA GENERATION"
    )
    print("=" * 72)

    validate_generation_config()
    ensure_generation_directories()

    categories = load_dataset(
        INPUT_FILES["categories"]
    )

    products = load_dataset(
        INPUT_FILES["products"]
    )

    stores = load_dataset(
        INPUT_FILES["stores"]
    )

    datasets = (
        generate_promotion_datasets(
            categories=categories,
            products=products,
            stores=stores,
        )
    )

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():

        output_file = OUTPUT_FILES[
            dataset_name
        ]

        output_path = (
            CONFIG.output_directory
            / output_file
        )

        save_dataset(
            dataframe=dataframe,
            output_path=output_path,
        )

        print(
            f"{dataset_name:<25}"
            f"{len(dataframe):>8,} rows"
            f"  -> {output_file}"
        )

    promotions = datasets[
        "promotions"
    ]

    print("-" * 72)

    type_counts = (
        promotions[
            "PromotionType"
        ]
        .value_counts()
        .sort_index()
    )

    print("Promotion types:")

    for (
        promotion_type,
        count,
    ) in type_counts.items():
        print(
            f"  "
            f"{promotion_type:<12}"
            f"{count:>4}"
        )

    print("-" * 72)
    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 72)


if __name__ == "__main__":
    main()