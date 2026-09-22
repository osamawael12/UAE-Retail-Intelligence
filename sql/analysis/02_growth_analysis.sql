/*
============================================================
 UAE Retail Intelligence Platform
 File: 02_growth_analysis.sql

 Advanced Time-Series SQL Analysis:
 - Monthly Revenue
 - MoM Growth
 - YoY Growth
 - Running Revenue
 - 3-Month Moving Average
 - Revenue Ranking
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   Build Monthly Net Revenue
   ========================================================= */

WITH MonthlySales AS
(
    SELECT
        DATEFROMPARTS(
            YEAR(o.OrderDateTime),
            MONTH(o.OrderDateTime),
            1
        ) AS MonthStart,

        SUM(i.NetAmount)
            AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        DATEFROMPARTS(
            YEAR(o.OrderDateTime),
            MONTH(o.OrderDateTime),
            1
        )
),

MonthlyReturns AS
(
    SELECT
        DATEFROMPARTS(
            YEAR(o.OrderDateTime),
            MONTH(o.OrderDateTime),
            1
        ) AS MonthStart,

        SUM(
            ri.ReturnedNetAmount
        ) AS Returns

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    INNER JOIN sales.SalesOrderItem i
        ON ri.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        DATEFROMPARTS(
            YEAR(o.OrderDateTime),
            MONTH(o.OrderDateTime),
            1
        )
),

MonthlyRevenue AS
(
    SELECT
        s.MonthStart,

        s.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue

    FROM MonthlySales s

    LEFT JOIN MonthlyReturns r
        ON s.MonthStart
           = r.MonthStart
),

Comparison AS
(
    SELECT
        MonthStart,

        Revenue,

        LAG(
            Revenue,
            1
        ) OVER
        (
            ORDER BY MonthStart
        ) AS PreviousMonthRevenue,

        LAG(
            Revenue,
            12
        ) OVER
        (
            ORDER BY MonthStart
        ) AS PreviousYearRevenue,

        SUM(
            Revenue
        ) OVER
        (
            ORDER BY MonthStart
            ROWS BETWEEN
            UNBOUNDED PRECEDING
            AND CURRENT ROW
        ) AS RunningRevenue,

        AVG(
            Revenue
        ) OVER
        (
            ORDER BY MonthStart

            ROWS BETWEEN
            2 PRECEDING
            AND CURRENT ROW
        ) AS ThreeMonthMovingAverage,

        RANK() OVER
        (
            ORDER BY Revenue DESC
        ) AS RevenueRank

    FROM MonthlyRevenue
)

SELECT
    MonthStart,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        PreviousMonthRevenue
        AS DECIMAL(19,2)
    ) AS PreviousMonthRevenue,

    CAST(
        (
            Revenue
            - PreviousMonthRevenue
        )
        * 100.0
        / NULLIF(
            PreviousMonthRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS MoMGrowthPct,

    CAST(
        PreviousYearRevenue
        AS DECIMAL(19,2)
    ) AS PreviousYearRevenue,

    CAST(
        (
            Revenue
            - PreviousYearRevenue
        )
        * 100.0
        / NULLIF(
            PreviousYearRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS YoYGrowthPct,

    CAST(
        RunningRevenue
        AS DECIMAL(19,2)
    ) AS RunningRevenue,

    CAST(
        ThreeMonthMovingAverage
        AS DECIMAL(19,2)
    ) AS ThreeMonthMovingAverage,

    RevenueRank

FROM Comparison

ORDER BY
    MonthStart;
GO


/* =========================================================
   Annual Revenue + YoY
   ========================================================= */

WITH AnnualSales AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

AnnualReturns AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            ri.ReturnedNetAmount
        ) AS Returns

    FROM sales.ReturnItem ri

    JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    JOIN sales.SalesOrderItem i
        ON ri.OrderItemId
           = i.OrderItemId

    JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

AnnualRevenue AS
(
    SELECT
        s.SalesYear,

        s.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue

    FROM AnnualSales s

    LEFT JOIN AnnualReturns r
        ON s.SalesYear
           = r.SalesYear
),

Growth AS
(
    SELECT
        SalesYear,
        Revenue,

        LAG(
            Revenue
        ) OVER
        (
            ORDER BY SalesYear
        ) AS PreviousYearRevenue

    FROM AnnualRevenue
)

SELECT
    SalesYear,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        PreviousYearRevenue
        AS DECIMAL(19,2)
    ) AS PreviousYearRevenue,

    CAST(
        (
            Revenue
            - PreviousYearRevenue
        )
        * 100.0
        / NULLIF(
            PreviousYearRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS YoYGrowthPct

FROM Growth

ORDER BY SalesYear;
GO