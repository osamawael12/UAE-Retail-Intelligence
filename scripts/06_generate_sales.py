"""
Generate synthetic sales transactions.

Required generated datasets from Steps 01-05.

Outputs:
- sales_orders.csv
- sales_order_items.csv
- sales_order_payments.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.sales_generator import (
    generate_sales_datasets,
)


INPUT_FILES = {
    "dates": "core_date_dimension.csv",
    "stores": "core_stores.csv",
    "cities": "core_cities.csv",
    "customers": "customer_customers.csv",
    "customer_profiles": (
        "customer_simulation_profiles.csv"
    ),
    "sales_channels": (
        "core_sales_channels.csv"
    ),
    "payment_methods": (
        "core_payment_methods.csv"
    ),
    "products": "product_products.csv",
    "subcategories": (
        "product_subcategories.csv"
    ),
    "promotions": "sales_promotions.csv",
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


OUTPUT_FILES = {
    "orders": "sales_orders.csv",
    "order_items": (
        "sales_order_items.csv"
    ),
    "order_payments": (
        "sales_order_payments.csv"
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
        "STEP 06 - SALES DATA GENERATION"
    )
    print("=" * 72)

    validate_generation_config()
    ensure_generation_directories()

    datasets_in = {
        name: load_dataset(
            file_name
        )
        for name, file_name
        in INPUT_FILES.items()
    }

    sales = generate_sales_datasets(
        dates=datasets_in["dates"],
        stores=datasets_in["stores"],
        cities=datasets_in["cities"],
        customers=(
            datasets_in["customers"]
        ),
        customer_profiles=(
            datasets_in[
                "customer_profiles"
            ]
        ),
        sales_channels=(
            datasets_in[
                "sales_channels"
            ]
        ),
        payment_methods=(
            datasets_in[
                "payment_methods"
            ]
        ),
        products=(
            datasets_in["products"]
        ),
        subcategories=(
            datasets_in[
                "subcategories"
            ]
        ),
        promotions=(
            datasets_in[
                "promotions"
            ]
        ),
        promotion_products=(
            datasets_in[
                "promotion_products"
            ]
        ),
        promotion_categories=(
            datasets_in[
                "promotion_categories"
            ]
        ),
        promotion_stores=(
            datasets_in[
                "promotion_stores"
            ]
        ),
    )

    for name, dataframe in (
        sales.items()
    ):
        output_file = (
            OUTPUT_FILES[name]
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
            f"{name:<25}"
            f"{len(dataframe):>10,} rows"
            f" -> {output_file}"
        )

    orders = sales["orders"]
    items = sales["order_items"]

    print("-" * 72)

    print(
        "Average items/order : "
        f"{len(items) / len(orders):.2f}"
    )

    print(
        "Gross sales         : "
        f"AED "
        f"{pd.to_numeric(items['GrossAmount']).sum():,.2f}"
    )

    print(
        "Discounts           : "
        f"AED "
        f"{pd.to_numeric(items['DiscountAmount']).sum():,.2f}"
    )

    print(
        "Net sales           : "
        f"AED "
        f"{pd.to_numeric(items['NetAmount']).sum():,.2f}"
    )

    print(
        "VAT                 : "
        f"AED "
        f"{pd.to_numeric(items['VATAmount']).sum():,.2f}"
    )

    print(
        "COGS                : "
        f"AED "
        f"{pd.to_numeric(items['LineCOGS']).sum():,.2f}"
    )

    print("-" * 72)
    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 72)


if __name__ == "__main__":
    main()