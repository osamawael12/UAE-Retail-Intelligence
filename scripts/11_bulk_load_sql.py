"""
UAE Retail Intelligence Platform
STEP 11 - SQL Server Bulk Load

Prerequisite:
Step 10 Full Data Quality must pass.

Loads generated datasets into existing SQL Server tables.
"""

from config.generation_config import (
    CONFIG,
)
from src.database.bulk_loader import (
    bulk_load_all,
)
from src.database.connection import (
    get_engine,
)
from src.validation.data_quality import (
    run_data_quality,
)


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 11 - SQL SERVER BULK LOAD"
    )
    print("=" * 78)

    print(
        "Running pre-load data quality..."
    )

    report, _ = run_data_quality(
        CONFIG.output_directory
    )

    if not report.is_valid:
        print(
            "DATA QUALITY FAILED."
        )
        print(
            "Bulk load cancelled."
        )
        raise SystemExit(1)

    print(
        "Pre-load data quality: PASSED"
    )
    print("-" * 78)

    engine = get_engine()

    print(
        "Loading SQL Server tables..."
    )

    loaded = bulk_load_all(
        engine=engine,
        data_directory=(
            CONFIG.output_directory
        ),
    )

    total_rows = sum(
        count
        for _, count
        in loaded
    )

    print("-" * 78)

    print(
        f"Tables loaded : "
        f"{len(loaded):,}"
    )

    print(
        f"Rows loaded   : "
        f"{total_rows:,}"
    )

    print("-" * 78)

    print(
        "SQL BULK LOAD: SUCCESS"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()