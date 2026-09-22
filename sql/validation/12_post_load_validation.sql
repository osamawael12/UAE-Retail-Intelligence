USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO

/* =========================================================
   POST-LOAD VALIDATION
   Any query returning rows indicates a problem.
   ========================================================= */


/* =========================================================
   1. Core expected counts
   ========================================================= */

SELECT 'Emirate' AS Entity, COUNT_BIG(*) 
FROM core.Emirate

UNION ALL
SELECT 'Store', COUNT_BIG(*)
FROM core.Store

UNION ALL
SELECT 'DateDimension', COUNT_BIG(*)
FROM core.DateDimension

UNION ALL
SELECT 'Employee', COUNT_BIG(*)
FROM core.Employee

UNION ALL
SELECT 'Category', COUNT_BIG(*)
FROM product.Category

UNION ALL
SELECT 'Brand', COUNT_BIG(*)
FROM product.Brand

UNION ALL
SELECT 'Supplier', COUNT_BIG(*)
FROM product.Supplier

UNION ALL
SELECT 'Product', COUNT_BIG(*)
FROM product.Product

UNION ALL
SELECT 'Customer', COUNT_BIG(*)
FROM customer.Customer

UNION ALL
SELECT 'SalesOrder', COUNT_BIG(*)
FROM sales.SalesOrder

UNION ALL
SELECT 'StoreMonthlyTarget', COUNT_BIG(*)
FROM sales.StoreMonthlyTarget;
GO


/* =========================================================
   2. Orders without items
   Expected: 0
   ========================================================= */

SELECT
    o.OrderId
FROM sales.SalesOrder o
LEFT JOIN sales.SalesOrderItem i
    ON o.OrderId = i.OrderId
WHERE i.OrderItemId IS NULL;
GO


/* =========================================================
   3. Order Items without valid Orders
   Expected: 0
   ========================================================= */

SELECT
    i.OrderItemId
FROM sales.SalesOrderItem i
LEFT JOIN sales.SalesOrder o
    ON i.OrderId = o.OrderId
WHERE o.OrderId IS NULL;
GO


/* =========================================================
   4. Invalid Product references
   Expected: 0
   ========================================================= */

SELECT
    i.OrderItemId
FROM sales.SalesOrderItem i
LEFT JOIN product.Product p
    ON i.ProductId = p.ProductId
WHERE p.ProductId IS NULL;
GO


/* =========================================================
   5. Sales line financial validation
   Expected: 0
   ========================================================= */

SELECT
    OrderItemId,
    GrossAmount,
    DiscountAmount,
    NetAmount,
    VATAmount,
    CustomerTotal,
    LineCOGS
FROM sales.SalesOrderItem
WHERE
       GrossAmount <> ROUND(UnitPrice * Quantity, 4)

    OR NetAmount <> ROUND(
        GrossAmount - DiscountAmount,
        4
    )

    OR VATAmount <> ROUND(
        NetAmount * VATRate,
        4
    )

    OR CustomerTotal <> ROUND(
        NetAmount + VATAmount,
        4
    )

    OR LineCOGS <> ROUND(
        UnitCost * Quantity,
        4
    );
GO


/* =========================================================
   6. Order Header vs Items
   Expected: 0
   ========================================================= */

WITH ItemTotals AS
(
    SELECT
        OrderId,

        SUM(GrossAmount)
            AS GrossAmount,

        SUM(DiscountAmount)
            AS DiscountAmount,

        SUM(NetAmount)
            AS NetAmount,

        SUM(VATAmount)
            AS VATAmount,

        SUM(CustomerTotal)
            AS CustomerTotal

    FROM sales.SalesOrderItem

    GROUP BY OrderId
)

SELECT
    o.OrderId
FROM sales.SalesOrder o
JOIN ItemTotals i
    ON o.OrderId = i.OrderId
WHERE
       o.GrossAmount <> i.GrossAmount
    OR o.DiscountAmount <> i.DiscountAmount
    OR o.NetAmount <> i.NetAmount
    OR o.VATAmount <> i.VATAmount
    OR o.CustomerTotal <> i.CustomerTotal;
GO


/* =========================================================
   7. Payment reconciliation
   Expected: 0
   ========================================================= */

WITH PaymentTotals AS
(
    SELECT
        OrderId,
        SUM(PaymentAmount)
            AS PaymentAmount
    FROM sales.OrderPayment
    GROUP BY OrderId
)

SELECT
    o.OrderId
FROM sales.SalesOrder o
LEFT JOIN PaymentTotals p
    ON o.OrderId = p.OrderId
WHERE
       p.OrderId IS NULL
    OR o.CustomerTotal
        <> p.PaymentAmount;
GO


/* =========================================================
   8. Return before sale
   Expected: 0
   ========================================================= */

SELECT
    r.ReturnId,
    r.OrderId,
    o.OrderDateTime,
    r.ReturnDateTime
FROM sales.[Return] r
JOIN sales.SalesOrder o
    ON r.OrderId = o.OrderId
WHERE
    r.ReturnDateTime
    < o.OrderDateTime;
GO


/* =========================================================
   9. Returned quantity greater than sold quantity
   Expected: 0
   ========================================================= */

WITH ReturnedQuantity AS
(
    SELECT
        OrderItemId,

        SUM(ReturnQuantity)
            AS ReturnedQuantity

    FROM sales.ReturnItem

    GROUP BY OrderItemId
)

SELECT
    i.OrderItemId,
    i.Quantity AS SoldQuantity,
    r.ReturnedQuantity

FROM ReturnedQuantity r

JOIN sales.SalesOrderItem i
    ON r.OrderItemId
       = i.OrderItemId

WHERE
    r.ReturnedQuantity
    > i.Quantity;
GO


/* =========================================================
   10. Return header reconciliation
   Expected: 0
   ========================================================= */

WITH ReturnTotals AS
(
    SELECT
        ReturnId,

        SUM(ReturnedNetAmount)
            AS ReturnedNetAmount,

        SUM(VATReversed)
            AS VATReversed,

        SUM(RefundAmount)
            AS RefundAmount

    FROM sales.ReturnItem

    GROUP BY ReturnId
)

SELECT
    r.ReturnId

FROM sales.[Return] r

JOIN ReturnTotals x
    ON r.ReturnId
       = x.ReturnId

WHERE
       r.TotalReturnNetAmount
            <> x.ReturnedNetAmount

    OR r.TotalVATReversed
            <> x.VATReversed

    OR r.TotalRefundAmount
            <> x.RefundAmount;
GO


/* =========================================================
   11. Refund reconciliation
   Expected: 0
   ========================================================= */

WITH RefundTotals AS
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

SELECT
    r.ReturnId

FROM sales.[Return] r

LEFT JOIN RefundTotals f
    ON r.ReturnId
       = f.ReturnId

WHERE
    r.ReturnStatus = 'COMPLETED'
    AND
    (
        f.ReturnId IS NULL
        OR
        r.TotalRefundAmount
        <> f.RefundAmount
    );
GO


/* =========================================================
   12. SALE movement mapping
   Expected: 0
   ========================================================= */

SELECT
    i.OrderItemId

FROM sales.SalesOrderItem i

LEFT JOIN inventory.InventoryMovement m
    ON i.OrderItemId
       = m.OrderItemId

    AND m.MovementType
        = 'SALE'

WHERE
    m.InventoryMovementId
    IS NULL;
GO


/* =========================================================
   13. Invalid inventory movement signs
   Expected: 0
   ========================================================= */

SELECT
    InventoryMovementId,
    MovementType,
    QuantityChange

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

    OR QuantityChange = 0;
GO


/* =========================================================
   14. Final inventory vs ledger
   Expected: 0
   ========================================================= */

WITH Ledger AS
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

SELECT
    i.StoreId,
    i.ProductId,
    i.CurrentStock,
    COALESCE(
        l.LedgerStock,
        0
    ) AS LedgerStock

FROM inventory.StoreProductInventory i

LEFT JOIN Ledger l
    ON i.StoreId
       = l.StoreId
    AND i.ProductId
       = l.ProductId

WHERE
    i.CurrentStock
    <> COALESCE(
        l.LedgerStock,
        0
    );
GO


/* =========================================================
   15. Negative final stock
   Expected: 0
   ========================================================= */

SELECT
    StoreId,
    ProductId,
    CurrentStock

FROM inventory.StoreProductInventory

WHERE
    CurrentStock < 0;
GO


/* =========================================================
   16. Monthly Target duplicates
   Expected: 0
   ========================================================= */

SELECT
    StoreId,
    TargetYear,
    TargetMonth,
    COUNT(*) AS DuplicateCount

FROM sales.StoreMonthlyTarget

GROUP BY
    StoreId,
    TargetYear,
    TargetMonth

HAVING COUNT(*) > 1;
GO


/* =========================================================
   17. Stores without 36 targets
   Expected: 0
   ========================================================= */

SELECT
    s.StoreId,
    COUNT(t.StoreMonthlyTargetId)
        AS TargetCount

FROM core.Store s

LEFT JOIN sales.StoreMonthlyTarget t
    ON s.StoreId
       = t.StoreId

GROUP BY s.StoreId

HAVING
    COUNT(
        t.StoreMonthlyTargetId
    ) <> 36;
GO


/* =========================================================
   18. Business financial summary
   Informational result
   ========================================================= */

WITH SalesTotals AS
(
    SELECT

        SUM(NetAmount)
            AS NetSalesBeforeReturns,

        SUM(LineCOGS)
            AS SalesCOGS,

        SUM(VATAmount)
            AS VATCollected,

        SUM(DiscountAmount)
            AS Discounts

    FROM sales.SalesOrderItem
),

ReturnTotals AS
(
    SELECT

        COALESCE(
            SUM(ReturnedNetAmount),
            0
        ) AS ReturnedNetSales,

        COALESCE(
            SUM(VATReversed),
            0
        ) AS VATReversed

    FROM sales.ReturnItem
),

ReturnedCost AS
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

    s.NetSalesBeforeReturns,

    r.ReturnedNetSales,

    s.NetSalesBeforeReturns
        - r.ReturnedNetSales
        AS Revenue,

    s.SalesCOGS,

    c.ReturnedCOGS,

    s.SalesCOGS
        - c.ReturnedCOGS
        AS NetCOGS,

    (
        s.NetSalesBeforeReturns
        - r.ReturnedNetSales
    )
    -
    (
        s.SalesCOGS
        - c.ReturnedCOGS
    )
        AS GrossProfit,

    s.VATCollected,

    r.VATReversed,

    s.Discounts

FROM SalesTotals s
CROSS JOIN ReturnTotals r
CROSS JOIN ReturnedCost c;
GO