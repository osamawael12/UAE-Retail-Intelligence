"""
UAE Retail Intelligence Platform
STEP 10 - Full Data Quality Pipeline

Runs critical validation against all generated business datasets.

Exit code:
0 = PASSED
1 = FAILED
"""

from config.generation_config import (
    CONFIG,
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
        "STEP 10 - FULL DATA QUALITY"
    )
    print("=" * 78)

    report, datasets = (
        run_data_quality(
            CONFIG.output_directory
        )
    )

    print()

    for result in (
        report.results
    ):
        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{result.check_name}"
        )

        print(
            f"       "
            f"{result.details}"
        )

    print()
    print("-" * 78)

    print(
        f"Checks Passed   : "
        f"{report.passed_count}"
    )

    print(
        f"Checks Failed   : "
        f"{report.failed_count}"
    )

    print(
        f"Datasets Loaded : "
        f"{len(datasets)}"
    )

    print("-" * 78)

    if not report.is_valid:
        print(
            "DATA QUALITY: FAILED"
        )

        print(
            "SQL bulk load is NOT allowed."
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "DATA QUALITY: PASSED"
    )

    print(
        "SQL bulk load is allowed."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()