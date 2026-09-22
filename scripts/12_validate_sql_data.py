"""
UAE Retail Intelligence Platform
STEP 12 - Post-Load SQL Validation

Validates data inside SQL Server after bulk loading.

All critical checks must return zero violations.
"""

from sqlalchemy import text

from src.database.connection import (
    get_engine,
)


CRITICAL_CHECKS = {
    "Orders without items": """
        SELECT COUNT_BIG(*)
        FROM sales.SalesOrder o
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM sales.SalesOrderItem i
            WHERE i.OrderId = o.OrderId
        )
    """,

    "Invalid sales financial lines": """
        SELECT COUNT_BIG(*)
        FROM sales.SalesOrderItem
        WHERE
               GrossAmount
                    <> ROUND(
                        UnitPrice * Quantity,
                        4
                    )
            OR NetAmount
                    <> ROUND(
                        GrossAmount
                        - DiscountAmount,
                        4
                    )
            OR VATAmount
                    <> ROUND(
                        NetAmount
                        * VATRate,
                        4
                    )
            OR CustomerTotal
                    <> ROUND(
                        NetAmount
                        + VATAmount,
                        4
                    )
            OR LineCOGS
                    <> ROUND(
                        UnitCost
                        * Quantity,
                        4
                    )
    """,

    "Order header mismatches": """
        WITH x AS
        (
            SELECT
                OrderId,
                SUM(GrossAmount) GrossAmount,
                SUM(DiscountAmount) DiscountAmount,
                SUM(NetAmount) NetAmount,
                SUM(VATAmount) VATAmount,
                SUM(CustomerTotal) CustomerTotal
            FROM sales.SalesOrderItem
            GROUP BY OrderId
        )
        SELECT COUNT_BIG(*)
        FROM sales.SalesOrder o
        JOIN x
            ON o.OrderId = x.OrderId
        WHERE
               o.GrossAmount
                    <> x.GrossAmount
            OR o.DiscountAmount
                    <> x.DiscountAmount
            OR o.NetAmount
                    <> x.NetAmount
            OR o.VATAmount
                    <> x.VATAmount
            OR o.CustomerTotal
                    <> x.CustomerTotal
    """,

    "Payment mismatches": """
        WITH x AS
        (
            SELECT
                OrderId,
                SUM(PaymentAmount)
                    AS PaymentAmount
            FROM sales.OrderPayment
            GROUP BY OrderId
        )
        SELECT COUNT_BIG(*)
        FROM sales.SalesOrder o
        LEFT JOIN x
            ON o.OrderId = x.OrderId
        WHERE
               x.OrderId IS NULL
            OR o.CustomerTotal
                <> x.PaymentAmount
    """,

    "Return before sale": """
        SELECT COUNT_BIG(*)
        FROM sales.[Return] r
        JOIN sales.SalesOrder o
            ON r.OrderId = o.OrderId
        WHERE
            r.ReturnDateTime
            < o.OrderDateTime
    """,

    "Returned quantity exceeds sold": """
        WITH x AS
        (
            SELECT
                OrderItemId,
                SUM(ReturnQuantity)
                    AS ReturnedQuantity
            FROM sales.ReturnItem
            GROUP BY OrderItemId
        )
        SELECT COUNT_BIG(*)
        FROM x
        JOIN sales.SalesOrderItem i
            ON x.OrderItemId
               = i.OrderItemId
        WHERE
            x.ReturnedQuantity
            > i.Quantity
    """,

    "Refund mismatches": """
        WITH x AS
        (
            SELECT
                ReturnId,
                SUM(RefundAmount)
                    AS RefundAmount
            FROM sales.Refund
            WHERE
                RefundStatus = 'COMPLETED'
            GROUP BY ReturnId
        )
        SELECT COUNT_BIG(*)
        FROM sales.[Return] r
        LEFT JOIN x
            ON r.ReturnId = x.ReturnId
        WHERE
            r.ReturnStatus = 'COMPLETED'
            AND
            (
                x.ReturnId IS NULL
                OR
                r.TotalRefundAmount
                    <> x.RefundAmount
            )
    """,

    "Sales without inventory movement": """
        SELECT COUNT_BIG(*)
        FROM sales.SalesOrderItem i
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM inventory.InventoryMovement m
            WHERE
                m.OrderItemId
                    = i.OrderItemId
                AND
                m.MovementType
                    = 'SALE'
        )
    """,

    "Invalid inventory movement signs": """
        SELECT COUNT_BIG(*)
        FROM inventory.InventoryMovement
        WHERE
               (
                    MovementType IN
                    (
                        'PURCHASE',
                        'RETURN',
                        'TRANSFER_IN'
                    )
                    AND QuantityChange <= 0
               )
            OR (
                    MovementType IN
                    (
                        'SALE',
                        'TRANSFER_OUT',
                        'DAMAGED'
                    )
                    AND QuantityChange >= 0
               )
            OR QuantityChange = 0
    """,

    "Inventory ledger mismatch": """
        WITH x AS
        (
            SELECT
                StoreId,
                ProductId,
                SUM(QuantityChange)
                    AS LedgerStock
            FROM inventory.InventoryMovement
            GROUP BY
                StoreId,
                ProductId
        )
        SELECT COUNT_BIG(*)
        FROM inventory.StoreProductInventory i
        LEFT JOIN x
            ON i.StoreId = x.StoreId
            AND i.ProductId = x.ProductId
        WHERE
            i.CurrentStock
            <> COALESCE(
                x.LedgerStock,
                0
            )
    """,

    "Negative final inventory": """
        SELECT COUNT_BIG(*)
        FROM inventory.StoreProductInventory
        WHERE CurrentStock < 0
    """,

    "Invalid store target count": """
        SELECT COUNT_BIG(*)
        FROM
        (
            SELECT
                s.StoreId
            FROM core.Store s
            LEFT JOIN sales.StoreMonthlyTarget t
                ON s.StoreId = t.StoreId
            GROUP BY s.StoreId
            HAVING
                COUNT(
                    t.StoreMonthlyTargetId
                ) <> 36
        ) x
    """,
}


EXPECTED_COUNTS = {
    "core.Emirate": 7,
    "core.Store": 25,
    "core.DateDimension": 1096,
    "core.Employee": 300,
    "product.Category": 8,
    "product.Brand": 60,
    "product.Supplier": 50,
    "product.Product": 800,
    "customer.Customer": 25_000,
    "sales.SalesOrder": 100_000,
    "sales.StoreMonthlyTarget": 900,
    "inventory.StoreProductInventory": 20_000,
}


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 12 - POST-LOAD SQL VALIDATION"
    )
    print("=" * 78)

    engine = get_engine()

    failures = 0

    with engine.connect() as connection:
        print(
            "\nExpected row counts:"
        )

        for (
            table,
            expected,
        ) in EXPECTED_COUNTS.items():

            actual = int(
                connection.execute(
                    text(
                        f"""
                        SELECT COUNT_BIG(*)
                        FROM {table}
                        """
                    )
                ).scalar_one()
            )

            passed = (
                actual == expected
            )

            status = (
                "PASS"
                if passed
                else "FAIL"
            )

            print(
                f"[{status}] "
                f"{table:<38}"
                f"{actual:>12,}"
            )

            if not passed:
                failures += 1

        print(
            "\nCritical SQL checks:"
        )

        for (
            check_name,
            query,
        ) in CRITICAL_CHECKS.items():

            violations = int(
                connection.execute(
                    text(query)
                ).scalar_one()
            )

            passed = (
                violations == 0
            )

            status = (
                "PASS"
                if passed
                else "FAIL"
            )

            print(
                f"[{status}] "
                f"{check_name:<45}"
                f"violations="
                f"{violations:,}"
            )

            if not passed:
                failures += 1

        summary = (
            connection.execute(
                text(
                    """
                    WITH SalesTotals AS
                    (
                        SELECT
                            SUM(NetAmount)
                                AS NetSales,

                            SUM(LineCOGS)
                                AS SalesCOGS,

                            SUM(VATAmount)
                                AS VAT,

                            SUM(DiscountAmount)
                                AS Discounts

                        FROM sales.SalesOrderItem
                    ),

                    ReturnTotals AS
                    (
                        SELECT
                            COALESCE(
                                SUM(
                                    ReturnedNetAmount
                                ),
                                0
                            ) AS Returns
                        FROM sales.ReturnItem
                    ),

                    ReturnCOGS AS
                    (
                        SELECT
                            COALESCE(
                                SUM(
                                    i.UnitCost
                                    * r.ReturnQuantity
                                ),
                                0
                            ) AS ReturnedCOGS

                        FROM sales.ReturnItem r

                        JOIN sales.SalesOrderItem i
                            ON r.OrderItemId
                               = i.OrderItemId
                    )

                    SELECT
                        s.NetSales,
                        r.Returns,

                        s.NetSales
                            - r.Returns
                            AS Revenue,

                        s.SalesCOGS
                            - c.ReturnedCOGS
                            AS NetCOGS,

                        (
                            s.NetSales
                            - r.Returns
                        )
                        -
                        (
                            s.SalesCOGS
                            - c.ReturnedCOGS
                        )
                            AS GrossProfit,

                        s.VAT,

                        s.Discounts

                    FROM SalesTotals s
                    CROSS JOIN ReturnTotals r
                    CROSS JOIN ReturnCOGS c
                    """
                )
            )
            .mappings()
            .one()
        )

    print(
        "\nBusiness financial summary:"
    )

    for key in [
        "NetSales",
        "Returns",
        "Revenue",
        "NetCOGS",
        "GrossProfit",
        "VAT",
        "Discounts",
    ]:
        value = float(
            summary[key] or 0
        )

        print(
            f"  "
            f"{key:<15}"
            f"AED {value:>18,.2f}"
        )

    print()
    print("-" * 78)

    if failures:
        print(
            f"Failed checks : "
            f"{failures}"
        )

        print(
            "POST-LOAD VALIDATION: FAILED"
        )

        print(
            "Do not continue to analytics."
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "Failed checks : 0"
    )

    print(
        "POST-LOAD VALIDATION: PASSED"
    )

    print(
        "Database is ready for analytics."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()