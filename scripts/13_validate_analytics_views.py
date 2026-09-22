"""
UAE Retail Intelligence Platform
STEP 13 - Analytics Views Validation

Validates:
- Required views exist
- Expected view grains
- SalesDetail does not duplicate sales lines
- Revenue reconciles across analytics views
- Gross Profit reconciles
- Customer360 contains all customers
- InventoryStatus contains all Store x Product rows
- TargetPerformance contains all 900 targets
"""

from decimal import Decimal

from sqlalchemy import text

from src.database.connection import (
    get_engine,
)


EXPECTED_VIEWS = {
    "vw_SalesDetail",
    "vw_DailySales",
    "vw_StorePerformance",
    "vw_ProductPerformance",
    "vw_Customer360",
    "vw_ReturnAnalysis",
    "vw_InventoryStatus",
    "vw_TargetPerformance",
}


EXPECTED_REVENUE = Decimal(
    "222709720.48"
)


def decimal_2(
    value,
) -> Decimal:
    return Decimal(
        str(value)
    ).quantize(
        Decimal("0.01")
    )


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 13 - ANALYTICS VIEWS VALIDATION"
    )
    print("=" * 78)

    engine = get_engine()

    failures = 0

    with engine.connect() as connection:

        existing_views = set(
            connection.execute(
                text(
                    """
                    SELECT v.name
                    FROM sys.views v
                    INNER JOIN sys.schemas s
                        ON v.schema_id
                           = s.schema_id
                    WHERE
                        s.name = 'analytics'
                    """
                )
            ).scalars().all()
        )

        missing_views = (
            EXPECTED_VIEWS
            - existing_views
        )

        if missing_views:
            failures += 1

            print(
                "[FAIL] Required views"
            )

            print(
                "       Missing: "
                + ", ".join(
                    sorted(
                        missing_views
                    )
                )
            )

        else:
            print(
                "[PASS] Required views"
            )

            print(
                "       All 8 analytics "
                "views exist"
            )

        print()

        # ----------------------------------------------------
        # SalesDetail Grain
        # ----------------------------------------------------

        order_items = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM sales.SalesOrderItem
                    """
                )
            ).scalar_one()
        )

        sales_detail_rows = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM analytics.vw_SalesDetail
                    """
                )
            ).scalar_one()
        )

        if (
            order_items
            == sales_detail_rows
        ):
            print(
                "[PASS] SalesDetail grain"
            )

            print(
                f"       "
                f"{sales_detail_rows:,} "
                "rows"
            )
        else:
            failures += 1

            print(
                "[FAIL] SalesDetail grain"
            )

            print(
                f"       OrderItems="
                f"{order_items:,}, "
                f"View="
                f"{sales_detail_rows:,}"
            )

        print()

        # ----------------------------------------------------
        # Revenue and Profit
        # ----------------------------------------------------

        sales_metrics = (
            connection.execute(
                text(
                    """
                    SELECT
                        SUM(Revenue)
                            AS Revenue,

                        SUM(GrossProfit)
                            AS GrossProfit
                    FROM
                        analytics.vw_SalesDetail
                    """
                )
            )
            .mappings()
            .one()
        )

        store_metrics = (
            connection.execute(
                text(
                    """
                    SELECT
                        SUM(Revenue)
                            AS Revenue,

                        SUM(GrossProfit)
                            AS GrossProfit
                    FROM
                        analytics.vw_StorePerformance
                    """
                )
            )
            .mappings()
            .one()
        )

        product_metrics = (
            connection.execute(
                text(
                    """
                    SELECT
                        SUM(Revenue)
                            AS Revenue,

                        SUM(GrossProfit)
                            AS GrossProfit
                    FROM
                        analytics.vw_ProductPerformance
                    """
                )
            )
            .mappings()
            .one()
        )

        sales_revenue = decimal_2(
            sales_metrics[
                "Revenue"
            ]
        )

        store_revenue = decimal_2(
            store_metrics[
                "Revenue"
            ]
        )

        product_revenue = decimal_2(
            product_metrics[
                "Revenue"
            ]
        )

        revenue_passed = (
            sales_revenue
            == store_revenue
            == product_revenue
            == EXPECTED_REVENUE
        )

        if revenue_passed:
            print(
                "[PASS] Revenue reconciliation"
            )

            print(
                f"       AED "
                f"{sales_revenue:,.2f}"
            )
        else:
            failures += 1

            print(
                "[FAIL] Revenue reconciliation"
            )

            print(
                f"       SalesDetail="
                f"{sales_revenue}, "
                f"Store="
                f"{store_revenue}, "
                f"Product="
                f"{product_revenue}"
            )

        print()

        sales_profit = decimal_2(
            sales_metrics[
                "GrossProfit"
            ]
        )

        store_profit = decimal_2(
            store_metrics[
                "GrossProfit"
            ]
        )

        product_profit = decimal_2(
            product_metrics[
                "GrossProfit"
            ]
        )

        profit_passed = (
            sales_profit
            == store_profit
            == product_profit
        )

        if profit_passed:
            print(
                "[PASS] Gross Profit reconciliation"
            )

            print(
                f"       AED "
                f"{sales_profit:,.2f}"
            )
        else:
            failures += 1

            print(
                "[FAIL] Gross Profit reconciliation"
            )

            print(
                f"       SalesDetail="
                f"{sales_profit}, "
                f"Store="
                f"{store_profit}, "
                f"Product="
                f"{product_profit}"
            )

        print()

        # ----------------------------------------------------
        # Customer 360
        # ----------------------------------------------------

        customers = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM customer.Customer
                    """
                )
            ).scalar_one()
        )

        customer360 = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM analytics.vw_Customer360
                    """
                )
            ).scalar_one()
        )

        if (
            customers
            == customer360
            == 25_000
        ):
            print(
                "[PASS] Customer360 grain"
            )

            print(
                "       25,000 customers"
            )
        else:
            failures += 1

            print(
                "[FAIL] Customer360 grain"
            )

            print(
                f"       Customer="
                f"{customers:,}, "
                f"View="
                f"{customer360:,}"
            )

        print()

        # ----------------------------------------------------
        # Return View
        # ----------------------------------------------------

        return_items = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM sales.ReturnItem
                    """
                )
            ).scalar_one()
        )

        return_view = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM analytics.vw_ReturnAnalysis
                    """
                )
            ).scalar_one()
        )

        if (
            return_items
            == return_view
        ):
            print(
                "[PASS] ReturnAnalysis grain"
            )

            print(
                f"       "
                f"{return_view:,} rows"
            )
        else:
            failures += 1

            print(
                "[FAIL] ReturnAnalysis grain"
            )

        print()

        # ----------------------------------------------------
        # Inventory
        # ----------------------------------------------------

        inventory_count = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM analytics.vw_InventoryStatus
                    """
                )
            ).scalar_one()
        )

        if inventory_count == 20_000:
            print(
                "[PASS] InventoryStatus grain"
            )

            print(
                "       20,000 Store/Product rows"
            )
        else:
            failures += 1

            print(
                "[FAIL] InventoryStatus grain"
            )

            print(
                f"       "
                f"{inventory_count:,} rows"
            )

        print()

        # ----------------------------------------------------
        # Targets
        # ----------------------------------------------------

        target_count = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM analytics.vw_TargetPerformance
                    """
                )
            ).scalar_one()
        )

        if target_count == 900:
            print(
                "[PASS] TargetPerformance grain"
            )

            print(
                "       900 Store/Month rows"
            )
        else:
            failures += 1

            print(
                "[FAIL] TargetPerformance grain"
            )

            print(
                f"       "
                f"{target_count:,} rows"
            )

    print()
    print("-" * 78)

    if failures:
        print(
            f"Failed checks : "
            f"{failures}"
        )

        print(
            "ANALYTICS VIEWS: FAILED"
        )

        print(
            "Do not continue to EDA."
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "Failed checks : 0"
    )

    print(
        "ANALYTICS VIEWS: PASSED"
    )

    print(
        "Analytics layer is ready."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()