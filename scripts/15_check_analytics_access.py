"""
UAE Retail Intelligence Platform
STEP 15A - Python Analytics Access Check
"""

from src.analytics.data_access import (
    get_company_daily_sales,
    get_customer_360,
    get_dataset_overview,
    get_executive_summary,
    get_inventory_status,
    get_monthly_company_sales,
    get_product_performance,
    get_returns,
    get_store_performance,
    get_target_performance,
)


EXPECTED_REVENUE = (
    222_709_720.48
)


def main() -> None:
    print("=" * 76)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "PYTHON ANALYTICS DATA ACCESS CHECK"
    )
    print("=" * 76)

    overview = (
        get_dataset_overview()
    )

    print(
        "\nAnalytics datasets:"
    )

    print(
        overview.to_string(
            index=False
        )
    )

    summary = (
        get_executive_summary()
    )

    revenue = float(
        summary[
            "Revenue"
        ]
    )

    print(
        "\nExecutive KPIs:"
    )

    print(
        f"Revenue      : "
        f"AED {revenue:,.2f}"
    )

    print(
        f"Gross Profit : "
        f"AED "
        f"{float(summary['GrossProfit']):,.2f}"
    )

    print(
        f"Margin       : "
        f"{float(summary['GrossMarginPct']):.2f}%"
    )

    print(
        f"Orders       : "
        f"{int(summary['Orders']):,}"
    )

    print(
        f"Customers    : "
        f"{int(summary['Customers']):,}"
    )

    if (
        round(
            revenue,
            2,
        )
        != EXPECTED_REVENUE
    ):
        raise RuntimeError(
            "Revenue reconciliation "
            "failed in Python."
        )

    daily = (
        get_company_daily_sales()
    )

    monthly = (
        get_monthly_company_sales()
    )

    stores = (
        get_store_performance()
    )

    products = (
        get_product_performance()
    )

    customers = (
        get_customer_360()
    )

    returns = (
        get_returns()
    )

    inventory = (
        get_inventory_status()
    )

    targets = (
        get_target_performance()
    )

    print(
        "\nPython analytical shapes:"
    )

    print(
        f"Daily       : {daily.shape}"
    )

    print(
        f"Monthly     : {monthly.shape}"
    )

    print(
        f"Stores      : {stores.shape}"
    )

    print(
        f"Products    : {products.shape}"
    )

    print(
        f"Customers   : {customers.shape}"
    )

    print(
        f"Returns     : {returns.shape}"
    )

    print(
        f"Inventory   : {inventory.shape}"
    )

    print(
        f"Targets     : {targets.shape}"
    )

    if len(daily) != 1096:
        raise RuntimeError(
            "Expected 1,096 company "
            "daily observations."
        )

    if len(monthly) != 36:
        raise RuntimeError(
            "Expected 36 monthly "
            "observations."
        )

    if len(stores) != 25:
        raise RuntimeError(
            "Expected 25 stores."
        )

    if len(customers) != 25_000:
        raise RuntimeError(
            "Expected 25,000 customers."
        )

    if len(inventory) != 20_000:
        raise RuntimeError(
            "Expected 20,000 inventory "
            "records."
        )

    if len(targets) != 900:
        raise RuntimeError(
            "Expected 900 target records."
        )

    print()
    print("-" * 76)
    print(
        "PYTHON ANALYTICS ACCESS: PASSED"
    )
    print("=" * 76)


if __name__ == "__main__":
    main()