"""
Generate synthetic retail returns and refunds.

Required:
- Sales datasets
- Customer datasets
- Product datasets
- Payment methods

Outputs:
- sales_returns.csv
- sales_return_items.csv
- sales_refunds.csv
- simulation_return_anomaly_manifest.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.return_generator import (
    generate_return_datasets,
)


INPUT_FILES = {
    "orders": (
        "sales_orders.csv"
    ),
    "order_items": (
        "sales_order_items.csv"
    ),
    "customers": (
        "customer_customers.csv"
    ),
    "customer_profiles": (
        "customer_simulation_profiles.csv"
    ),
    "products": (
        "product_products.csv"
    ),
    "subcategories": (
        "product_subcategories.csv"
    ),
    "categories": (
        "product_categories.csv"
    ),
    "payment_methods": (
        "core_payment_methods.csv"
    ),
}


OUTPUT_FILES = {
    "returns": (
        "sales_returns.csv"
    ),
    "return_items": (
        "sales_return_items.csv"
    ),
    "refunds": (
        "sales_refunds.csv"
    ),
    "return_anomaly_manifest": (
        "simulation_return_anomaly_manifest.csv"
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

    return pd.read_csv(
        path
    )


def save_dataset(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    dataframe.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    print("=" * 72)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 07 - RETURNS DATA GENERATION"
    )
    print("=" * 72)

    validate_generation_config()
    ensure_generation_directories()

    inputs = {
        name: load_dataset(
            file_name
        )
        for (
            name,
            file_name,
        ) in INPUT_FILES.items()
    }

    datasets = (
        generate_return_datasets(
            orders=(
                inputs["orders"]
            ),
            order_items=(
                inputs[
                    "order_items"
                ]
            ),
            customers=(
                inputs["customers"]
            ),
            customer_profiles=(
                inputs[
                    "customer_profiles"
                ]
            ),
            products=(
                inputs["products"]
            ),
            subcategories=(
                inputs[
                    "subcategories"
                ]
            ),
            categories=(
                inputs["categories"]
            ),
            payment_methods=(
                inputs[
                    "payment_methods"
                ]
            ),
        )
    )

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():
        output_file = (
            OUTPUT_FILES[
                dataset_name
            ]
        )

        output_path = (
            CONFIG.output_directory
            / output_file
        )

        save_dataset(
            dataframe=dataframe,
            path=output_path,
        )

        print(
            f"{dataset_name:<28}"
            f"{len(dataframe):>9,} rows"
            f" -> {output_file}"
        )

    order_items = (
        inputs[
            "order_items"
        ]
    )

    return_items = (
        datasets[
            "return_items"
        ]
    )

    gross_units = (
        pd.to_numeric(
            order_items[
                "Quantity"
            ]
        ).sum()
    )

    returned_units = (
        pd.to_numeric(
            return_items[
                "ReturnQuantity"
            ]
        ).sum()
    )

    unit_return_rate = (
        returned_units
        / gross_units
        * 100
    )

    refund_amount = (
        pd.to_numeric(
            datasets[
                "refunds"
            ][
                "RefundAmount"
            ]
        ).sum()
    )

    print("-" * 72)

    print(
        f"Gross units sold   : "
        f"{gross_units:,.0f}"
    )

    print(
        f"Returned units     : "
        f"{returned_units:,.0f}"
    )

    print(
        f"Unit return rate   : "
        f"{unit_return_rate:.2f}%"
    )

    print(
        f"Refund amount      : "
        f"AED {refund_amount:,.2f}"
    )

    print("-" * 72)

    print(
        "Return reasons:"
    )

    reason_counts = (
        return_items[
            "ReturnReason"
        ]
        .value_counts()
    )

    for reason, count in (
        reason_counts.items()
    ):
        print(
            f"  "
            f"{reason:<22}"
            f"{count:>8,}"
        )

    print("-" * 72)
    print(
        "Validation: PASSED"
    )
    print(
        "Status: SUCCESS"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()