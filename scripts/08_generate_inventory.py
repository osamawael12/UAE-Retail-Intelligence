"""
UAE Retail Intelligence Platform
STEP 08 - Inventory Generation

Inputs:
- Stores
- Products
- Sales Orders
- Sales Order Items
- Returns
- Return Items

Outputs:
- inventory_store_product.csv
- inventory_movements.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.inventory_generator import (
    generate_inventory_datasets,
)


INPUT_FILES = {
    "stores": (
        "core_stores.csv"
    ),
    "products": (
        "product_products.csv"
    ),
    "orders": (
        "sales_orders.csv"
    ),
    "order_items": (
        "sales_order_items.csv"
    ),
    "returns": (
        "sales_returns.csv"
    ),
    "return_items": (
        "sales_return_items.csv"
    ),
}


OUTPUT_FILES = {
    "store_product_inventory": (
        "inventory_store_product.csv"
    ),
    "inventory_movements": (
        "inventory_movements.csv"
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
        "STEP 08 - INVENTORY DATA GENERATION"
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
        generate_inventory_datasets(
            stores=(
                inputs[
                    "stores"
                ]
            ),
            products=(
                inputs[
                    "products"
                ]
            ),
            orders=(
                inputs[
                    "orders"
                ]
            ),
            order_items=(
                inputs[
                    "order_items"
                ]
            ),
            returns=(
                inputs[
                    "returns"
                ]
            ),
            return_items=(
                inputs[
                    "return_items"
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
            f"{len(dataframe):>10,} rows"
            f" -> {output_file}"
        )

    inventory = (
        datasets[
            "store_product_inventory"
        ]
    )

    movements = (
        datasets[
            "inventory_movements"
        ]
    )

    print("-" * 72)

    print(
        "Movement types:"
    )

    movement_counts = (
        movements[
            "MovementType"
        ]
        .value_counts()
    )

    for (
        movement_type,
        count,
    ) in (
        movement_counts.items()
    ):
        print(
            f"  "
            f"{movement_type:<15}"
            f"{count:>10,}"
        )

    print("-" * 72)

    print(
        f"Current stock units : "
        f"{inventory['CurrentStock'].sum():,.0f}"
    )

    low_stock_count = int(
        (
            (
                inventory[
                    "CurrentStock"
                ]
                <= inventory[
                    "ReorderPoint"
                ]
            )
            & (
                inventory[
                    "CurrentStock"
                ]
                > 0
            )
        ).sum()
    )

    stockout_count = int(
        (
            inventory[
                "CurrentStock"
            ]
            <= 0
        ).sum()
    )

    print(
        f"Low-stock SKUs      : "
        f"{low_stock_count:,}"
    )

    print(
        f"Current stockouts   : "
        f"{stockout_count:,}"
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