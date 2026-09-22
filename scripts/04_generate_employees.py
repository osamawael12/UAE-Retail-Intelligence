"""
Generate employee master data.

Required input:
- core_stores.csv

Output:
- core_employees.csv

No SQL Server writes are performed.
"""

from pathlib import Path

import pandas as pd

from config.generation_config import (
    CONFIG,
    ensure_generation_directories,
    validate_generation_config,
)
from src.generators.employee_generator import (
    generate_employees,
)


INPUT_FILE = "core_stores.csv"

OUTPUT_FILE = "core_employees.csv"


def load_stores() -> pd.DataFrame:
    path = (
        CONFIG.output_directory
        / INPUT_FILE
    )

    if not path.exists():
        raise FileNotFoundError(
            "Required stores dataset "
            f"not found: {path}"
        )

    stores = pd.read_csv(
        path
    )

    required_columns = {
        "StoreId",
        "OpenDate",
        "FloorAreaSqM",
    }

    missing_columns = (
        required_columns
        - set(
            stores.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "core_stores.csv is missing "
            "required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    return stores


def save_employees(
    employees: pd.DataFrame,
    path: Path,
) -> None:
    employees.to_csv(
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
        "STEP 04 - EMPLOYEE DATA GENERATION"
    )
    print("=" * 70)

    validate_generation_config()
    ensure_generation_directories()

    stores = load_stores()

    employees = (
        generate_employees(
            stores=stores
        )
    )

    output_path = (
        CONFIG.output_directory
        / OUTPUT_FILE
    )

    save_employees(
        employees=employees,
        path=output_path,
    )

    print(
        f"{'employees':<25}"
        f"{len(employees):>8,} rows"
        f"  -> {OUTPUT_FILE}"
    )

    print("-" * 70)

    active_count = int(
        (
            employees["IsActive"]
            == 1
        ).sum()
    )

    inactive_count = int(
        (
            employees["IsActive"]
            == 0
        ).sum()
    )

    manager_count = int(
        (
            employees["JobTitle"]
            == "Store Manager"
        ).sum()
    )

    print(
        f"Active employees   : "
        f"{active_count:,}"
    )

    print(
        f"Inactive employees : "
        f"{inactive_count:,}"
    )

    print(
        f"Store managers     : "
        f"{manager_count:,}"
    )

    print("Validation: PASSED")
    print("Status: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()