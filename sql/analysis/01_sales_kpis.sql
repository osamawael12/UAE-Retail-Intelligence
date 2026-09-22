/*
============================================================
 UAE Retail Intelligence Platform
 File: 01_sales_kpis.sql

 Purpose:
 Core commercial and executive KPI analysis.

 Official KPI rules:
 - VAT is excluded from Revenue.
 - Returns reduce Revenue.
 - Returned merchandise reverses corresponding COGS.
 - Only COMPLETED sales are included.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. EXECUTIVE KPI SUMMARY
   ========================================================= */

WITH Sales AS
(
    SELECT
        SUM(i.NetAmount) AS NetSalesBeforeReturns,
        SUM(i.LineCOGS) AS SalesCOGS,
        SUM(i.Quantity) AS GrossUnitsSold,
        SUM(i.DiscountAmount) AS DiscountAmount,
        SUM(i.VATAmount) AS VATCollected
    FROM sales.SalesOrderItem i
    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId
    WHERE o.OrderStatus = 'COMPLETED'
),

Returns AS
(
    SELECT
        COALESCE(
            SUM(ri.ReturnedNetAmount),
            0
        ) AS ReturnedNetSales,

        COALESCE(
            SUM(ri.ReturnQuantity),
            0
        ) AS ReturnedUnits,

        COALESCE(
            SUM(
                oi.UnitCost
                * ri.ReturnQuantity
            ),
            0
        ) AS ReturnedCOGS,

        COALESCE(
            SUM(ri.RefundAmount),
            0
        ) AS RefundAmount
    FROM sales.ReturnItem ri
    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId
    INNER JOIN sales.SalesOrderItem oi
        ON ri.OrderItemId = oi.OrderItemId
    WHERE r.ReturnStatus = 'COMPLETED'
),

Orders AS
(
    SELECT
        COUNT_BIG(*) AS Orders,
        COUNT_BIG(
            DISTINCT CustomerId
        ) AS Customers
    FROM sales.SalesOrder
    WHERE OrderStatus = 'COMPLETED'
),

Metrics AS
(
    SELECT
        s.NetSalesBeforeReturns,
        r.ReturnedNetSales,

        s.NetSalesBeforeReturns
            - r.ReturnedNetSales
            AS Revenue,

        s.SalesCOGS
            - r.ReturnedCOGS
            AS NetCOGS,

        (
            s.NetSalesBeforeReturns
            - r.ReturnedNetSales
        )
        -
        (
            s.SalesCOGS
            - r.ReturnedCOGS
        ) AS GrossProfit,

        s.GrossUnitsSold,

        s.GrossUnitsSold
            - r.ReturnedUnits
            AS NetUnitsSold,

        r.ReturnedUnits,

        s.DiscountAmount,

        s.VATCollected,

        r.RefundAmount,

        o.Orders,

        o.Customers

    FROM Sales s
    CROSS JOIN Returns r
    CROSS JOIN Orders o
)

SELECT
    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        GrossProfit
        AS DECIMAL(19,2)
    ) AS GrossProfit,

    CAST(
        CASE
            WHEN Revenue = 0
                THEN 0
            ELSE
                GrossProfit
                / Revenue
                * 100.0
        END
        AS DECIMAL(10,2)
    ) AS GrossMarginPct,

    Orders,

    Customers,

    GrossUnitsSold,

    NetUnitsSold,

    ReturnedUnits,

    CAST(
        CASE
            WHEN Orders = 0
                THEN 0
            ELSE
                Revenue
                / Orders
        END
        AS DECIMAL(19,2)
    ) AS AOV,

    CAST(
        CASE
            WHEN GrossUnitsSold = 0
                THEN 0
            ELSE
                ReturnedUnits
                * 100.0
                / GrossUnitsSold
        END
        AS DECIMAL(10,2)
    ) AS UnitReturnRatePct,

    CAST(
        DiscountAmount
        AS DECIMAL(19,2)
    ) AS DiscountAmount,

    CAST(
        RefundAmount
        AS DECIMAL(19,2)
    ) AS RefundAmount,

    CAST(
        VATCollected
        AS DECIMAL(19,2)
    ) AS VATCollected

FROM Metrics;
GO


/* =========================================================
   2. KPI SUMMARY BY YEAR

   Returns are attributed back to the original sale period
   for commercial performance reporting.
   ========================================================= */

WITH SalesByYear AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(i.NetAmount)
            AS NetSalesBeforeReturns,

        SUM(i.LineCOGS)
            AS SalesCOGS,

        SUM(i.Quantity)
            AS GrossUnits,

        SUM(i.DiscountAmount)
            AS DiscountAmount,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        COUNT_BIG(
            DISTINCT o.CustomerId
        ) AS Customers

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

ReturnsByYear AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits,

        SUM(
            oi.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

    INNER JOIN sales.SalesOrderItem oi
        ON ri.OrderItemId
           = oi.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON oi.OrderId
           = o.OrderId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

Yearly AS
(
    SELECT
        s.SalesYear,

        s.NetSalesBeforeReturns
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
            AS Revenue,

        (
            s.NetSalesBeforeReturns
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
        )
        -
        (
            s.SalesCOGS
            - COALESCE(
                r.ReturnedCOGS,
                0
            )
        )
            AS GrossProfit,

        s.Orders,

        s.Customers,

        s.GrossUnits,

        s.GrossUnits
            - COALESCE(
                r.ReturnedUnits,
                0
            )
            AS NetUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits,

        s.DiscountAmount

    FROM SalesByYear s

    LEFT JOIN ReturnsByYear r
        ON s.SalesYear
           = r.SalesYear
)

SELECT
    SalesYear,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        GrossProfit
        AS DECIMAL(19,2)
    ) AS GrossProfit,

    CAST(
        GrossProfit
        * 100.0
        / NULLIF(
            Revenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS GrossMarginPct,

    Orders,

    Customers,

    NetUnits,

    CAST(
        Revenue
        / NULLIF(
            Orders,
            0
        )
        AS DECIMAL(19,2)
    ) AS AOV,

    CAST(
        ReturnedUnits
        * 100.0
        / NULLIF(
            GrossUnits,
            0
        )
        AS DECIMAL(10,2)
    ) AS ReturnRatePct,

    CAST(
        DiscountAmount
        AS DECIMAL(19,2)
    ) AS DiscountAmount

FROM Yearly

ORDER BY SalesYear;
GO


/* =========================================================
   3. MONTHLY BUSINESS PERFORMANCE
   ========================================================= */

WITH MonthlySales AS
(
    SELECT
        DATEFROMPARTS(
            YEAR(
                o.OrderDateTime
            ),
            MONTH(
                o.OrderDateTime
            ),
            1
        ) AS MonthStart,

        SUM(
            i.NetAmount
        ) AS NetSales,

        SUM(
            i.LineCOGS
        ) AS SalesCOGS,

        SUM(
            i.Quantity
        ) AS GrossUnits,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        COUNT_BIG(
            DISTINCT o.CustomerId
        ) AS Customers

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        DATEFROMPARTS(
            YEAR(
                o.OrderDateTime
            ),
            MONTH(
                o.OrderDateTime
            ),
            1
        )
),

MonthlyReturns AS
(
    SELECT
        DATEFROMPARTS(
            YEAR(
                o.OrderDateTime
            ),
            MONTH(
                o.OrderDateTime
            ),
            1
        ) AS MonthStart,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits,

        SUM(
            oi.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    INNER JOIN sales.SalesOrderItem oi
        ON ri.OrderItemId
           = oi.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON oi.OrderId
           = o.OrderId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        DATEFROMPARTS(
            YEAR(
                o.OrderDateTime
            ),
            MONTH(
                o.OrderDateTime
            ),
            1
        )
)

SELECT
    s.MonthStart,

    CAST(
        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        (
            s.NetSales
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
        )
        -
        (
            s.SalesCOGS
            - COALESCE(
                r.ReturnedCOGS,
                0
            )
        )
        AS DECIMAL(19,2)
    ) AS GrossProfit,

    s.Orders,

    s.Customers,

    s.GrossUnits
        - COALESCE(
            r.ReturnedUnits,
            0
        )
        AS NetUnits,

    CAST(
        (
            s.NetSales
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
        )
        / NULLIF(
            s.Orders,
            0
        )
        AS DECIMAL(19,2)
    ) AS AOV,

    CAST(
        COALESCE(
            r.ReturnedUnits,
            0
        )
        * 100.0
        / NULLIF(
            s.GrossUnits,
            0
        )
        AS DECIMAL(10,2)
    ) AS ReturnRatePct

FROM MonthlySales s

LEFT JOIN MonthlyReturns r
    ON s.MonthStart
       = r.MonthStart

ORDER BY
    s.MonthStart;
GO


/* =========================================================
   4. SALES BY CHANNEL
   ========================================================= */

WITH ChannelSales AS
(
    SELECT
        ch.ChannelName,

        SUM(
            i.NetAmount
        ) AS NetSales,

        SUM(
            i.LineCOGS
        ) AS SalesCOGS,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        SUM(
            i.Quantity
        ) AS Units

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    INNER JOIN core.SalesChannel ch
        ON o.SalesChannelId
           = ch.SalesChannelId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        ch.ChannelName
),

ChannelReturns AS
(
    SELECT
        ch.ChannelName,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            oi.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    INNER JOIN sales.SalesOrderItem oi
        ON ri.OrderItemId
           = oi.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON oi.OrderId
           = o.OrderId

    INNER JOIN core.SalesChannel ch
        ON o.SalesChannelId
           = ch.SalesChannelId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        ch.ChannelName
)

SELECT
    s.ChannelName,

    s.Orders,

    s.Units,

    CAST(
        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        (
            s.NetSales
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
        )
        -
        (
            s.SalesCOGS
            - COALESCE(
                r.ReturnedCOGS,
                0
            )
        )
        AS DECIMAL(19,2)
    ) AS GrossProfit

FROM ChannelSales s

LEFT JOIN ChannelReturns r
    ON s.ChannelName
       = r.ChannelName

ORDER BY
    Revenue DESC;
GO


/* =========================================================
   5. SALES BY PAYMENT METHOD
   ========================================================= */

SELECT
    pm.PaymentMethodName,

    COUNT_BIG(
        DISTINCT p.OrderId
    ) AS Orders,

    CAST(
        SUM(
            p.PaymentAmount
        )
        AS DECIMAL(19,2)
    ) AS CustomerPayments,

    CAST(
        AVG(
            p.PaymentAmount
        )
        AS DECIMAL(19,2)
    ) AS AveragePayment

FROM sales.OrderPayment p

INNER JOIN core.PaymentMethod pm
    ON p.PaymentMethodId
       = pm.PaymentMethodId

GROUP BY
    pm.PaymentMethodName

ORDER BY
    CustomerPayments DESC;
GO


/* =========================================================
   6. DISCOUNT ANALYSIS
   ========================================================= */

SELECT
    CASE
        WHEN i.DiscountAmount = 0
            THEN 'NO_DISCOUNT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.10
            THEN 'UNDER_10_PERCENT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.20
            THEN '10_TO_20_PERCENT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.30
            THEN '20_TO_30_PERCENT'

        ELSE
            '30_PERCENT_PLUS'
    END AS DiscountBand,

    COUNT_BIG(*)
        AS SalesLines,

    SUM(i.Quantity)
        AS Units,

    CAST(
        SUM(i.NetAmount)
        AS DECIMAL(19,2)
    ) AS NetSales,

    CAST(
        SUM(
            i.NetAmount
            - i.LineCOGS
        )
        AS DECIMAL(19,2)
    ) AS PreReturnGrossProfit

FROM sales.SalesOrderItem i

INNER JOIN sales.SalesOrder o
    ON i.OrderId
       = o.OrderId

WHERE
    o.OrderStatus
    = 'COMPLETED'

GROUP BY
    CASE
        WHEN i.DiscountAmount = 0
            THEN 'NO_DISCOUNT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.10
            THEN 'UNDER_10_PERCENT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.20
            THEN '10_TO_20_PERCENT'

        WHEN
            i.DiscountAmount
            / NULLIF(
                i.GrossAmount,
                0
            )
            < 0.30
            THEN '20_TO_30_PERCENT'

        ELSE
            '30_PERCENT_PLUS'
    END

ORDER BY
    NetSales DESC;
GO