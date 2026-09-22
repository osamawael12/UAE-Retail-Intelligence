"""
UAE Retail Intelligence Platform
STEP 09 - Store Monthly Targets

Inputs:
- Stores
- Orders
- Order Items
- Returns
- Return Items

Output:
- sales_store_monthly_targets.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.target_generator import (
    generate_targets,
)


INPUT_FILES = {
    "stores": (
        "core_stores.csv"
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


OUTPUT_FILE = (
    "sales_store_monthly_targets.csv"
)


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
    )


def main() -> None:
    print("=" * 72)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 09 - STORE TARGET GENERATION"
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

    targets = generate_targets(
        stores=(
            inputs[
                "stores"
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

    output_path = (
        CONFIG.output_directory
        / OUTPUT_FILE
    )

    save_dataset(
        dataframe=targets,
        path=output_path,
    )

    print(
        f"{'targets':<28}"
        f"{len(targets):>9,} rows"
        f" -> {OUTPUT_FILE}"
    )

    print("-" * 72)

    summary = (
        targets.groupby(
            "TargetYear"
        )
        .agg(
            RevenueTarget=(
                "RevenueTarget",
                lambda values:
                    pd.to_numeric(
                        values
                    ).sum(),
            ),
            ProfitTarget=(
                "GrossProfitTarget",
                lambda values:
                    pd.to_numeric(
                        values
                    ).sum(),
            ),
            OrdersTarget=(
                "OrdersTarget",
                "sum",
            ),
        )
    )

    print(
        "Annual target summary:"
    )

    print(
        summary.round(2)
    )

    print("-" * 72)

    monthly_counts = (
        targets.groupby(
            "StoreId"
        ).size()
    )

    print(
        "Stores             : "
        f"{targets['StoreId'].nunique():,}"
    )

    print(
        "Months per store   : "
        f"{monthly_counts.min()} "
        f"to "
        f"{monthly_counts.max()}"
    )

    print(
        "Total target rows  : "
        f"{len(targets):,}"
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