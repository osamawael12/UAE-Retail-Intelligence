/*
============================================================
 UAE Retail Intelligence Platform
 File: 08_target_analysis.sql

 Target Analytics

 Includes:
 - Monthly Actual vs Target
 - Revenue Achievement
 - Profit Achievement
 - Orders Achievement
 - Variance
 - Store Target Ranking
 - Underperforming Stores
 - Annual Target Performance

 Returns are attributed to original sale periods.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. BUILD MONTHLY STORE ACTUALS
   ========================================================= */

WITH MonthlySales AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        MONTH(
            o.OrderDateTime
        ) AS SalesMonth,

        SUM(
            i.NetAmount
        ) AS NetSales,

        SUM(
            i.LineCOGS
        ) AS SalesCOGS,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        ),
        MONTH(
            o.OrderDateTime
        )
),

MonthlyReturns AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        MONTH(
            o.OrderDateTime
        ) AS SalesMonth,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            i.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS

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
        o.StoreId,
        YEAR(
            o.OrderDateTime
        ),
        MONTH(
            o.OrderDateTime
        )
),

Actuals AS
(
    SELECT
        s.StoreId,
        s.SalesYear,
        s.SalesMonth,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Revenue,

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
        ) AS GrossProfit,

        s.Orders

    FROM MonthlySales s

    LEFT JOIN MonthlyReturns r
        ON s.StoreId
           = r.StoreId

        AND s.SalesYear
           = r.SalesYear

        AND s.SalesMonth
           = r.SalesMonth
)

SELECT
    t.TargetYear,
    t.TargetMonth,

    s.StoreCode,
    s.StoreName,

    e.EmirateName,

    CAST(
        a.Revenue
        AS DECIMAL(19,2)
    ) AS ActualRevenue,

    t.RevenueTarget,

    CAST(
        a.Revenue
        - t.RevenueTarget
        AS DECIMAL(19,2)
    ) AS RevenueVariance,

    CAST(
        a.Revenue
        * 100.0
        / NULLIF(
            t.RevenueTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenueAchievementPct,

    CAST(
        a.GrossProfit
        AS DECIMAL(19,2)
    ) AS ActualGrossProfit,

    t.GrossProfitTarget,

    CAST(
        a.GrossProfit
        - t.GrossProfitTarget
        AS DECIMAL(19,2)
    ) AS ProfitVariance,

    CAST(
        a.GrossProfit
        * 100.0
        / NULLIF(
            t.GrossProfitTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS ProfitAchievementPct,

    a.Orders
        AS ActualOrders,

    t.OrdersTarget,

    a.Orders
        - t.OrdersTarget
        AS OrdersVariance,

    CAST(
        a.Orders
        * 100.0
        / NULLIF(
            t.OrdersTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS OrdersAchievementPct

FROM sales.StoreMonthlyTarget t

INNER JOIN core.Store s
    ON t.StoreId = s.StoreId

INNER JOIN core.City city
    ON s.CityId = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

LEFT JOIN Actuals a
    ON t.StoreId
       = a.StoreId

    AND t.TargetYear
       = a.SalesYear

    AND t.TargetMonth
       = a.SalesMonth

ORDER BY
    t.TargetYear,
    t.TargetMonth,
    s.StoreCode;
GO


/* =========================================================
   2. ANNUAL ACTUAL VS TARGET
   ========================================================= */

WITH AnnualActual AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            i.NetAmount
        ) AS NetSales,

        SUM(
            i.LineCOGS
        ) AS SalesCOGS,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

AnnualReturn AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            i.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

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
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

AnnualTarget AS
(
    SELECT
        StoreId,
        TargetYear,

        SUM(
            RevenueTarget
        ) AS RevenueTarget,

        SUM(
            GrossProfitTarget
        ) AS GrossProfitTarget,

        SUM(
            OrdersTarget
        ) AS OrdersTarget

    FROM sales.StoreMonthlyTarget

    GROUP BY
        StoreId,
        TargetYear
),

Metrics AS
(
    SELECT
        a.StoreId,
        a.SalesYear,

        a.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Revenue,

        (
            a.NetSales
            - COALESCE(
                r.ReturnedNetSales,
                0
            )
        )
        -
        (
            a.SalesCOGS
            - COALESCE(
                r.ReturnedCOGS,
                0
            )
        ) AS GrossProfit,

        a.Orders,

        t.RevenueTarget,
        t.GrossProfitTarget,
        t.OrdersTarget

    FROM AnnualActual a

    LEFT JOIN AnnualReturn r
        ON a.StoreId
           = r.StoreId
        AND a.SalesYear
           = r.SalesYear

    INNER JOIN AnnualTarget t
        ON a.StoreId
           = t.StoreId
        AND a.SalesYear
           = t.TargetYear
),

Ranked AS
(
    SELECT
        *,

        RANK() OVER
        (
            PARTITION BY SalesYear

            ORDER BY
                Revenue
                / NULLIF(
                    RevenueTarget,
                    0
                )
                DESC
        ) AS AchievementRank

    FROM Metrics
)

SELECT
    r.SalesYear,

    s.StoreCode,
    s.StoreName,

    CAST(
        r.Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    r.RevenueTarget,

    CAST(
        r.Revenue
        * 100.0
        / NULLIF(
            r.RevenueTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenueAchievementPct,

    CAST(
        r.GrossProfit
        * 100.0
        / NULLIF(
            r.GrossProfitTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS ProfitAchievementPct,

    CAST(
        r.Orders
        * 100.0
        / NULLIF(
            r.OrdersTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS OrdersAchievementPct,

    r.AchievementRank

FROM Ranked r

INNER JOIN core.Store s
    ON r.StoreId = s.StoreId

ORDER BY
    r.SalesYear,
    r.AchievementRank;
GO


/* =========================================================
   3. UNDERPERFORMING STORE MONTHS
   ========================================================= */

WITH MonthlyActual AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        MONTH(
            o.OrderDateTime
        ) AS SalesMonth,

        SUM(
            i.NetAmount
        )
        -
        COALESCE(
            SUM(
                CASE
                    WHEN ri.ReturnItemId
                         IS NOT NULL
                        THEN
                            ri.ReturnedNetAmount
                    ELSE 0
                END
            ),
            0
        ) AS ApproxRevenue

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    LEFT JOIN sales.ReturnItem ri
        ON i.OrderItemId
           = ri.OrderItemId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        ),
        MONTH(
            o.OrderDateTime
        )
)

SELECT TOP (30)

    t.TargetYear,
    t.TargetMonth,

    s.StoreCode,
    s.StoreName,

    CAST(
        a.ApproxRevenue
        AS DECIMAL(19,2)
    ) AS ActualRevenue,

    t.RevenueTarget,

    CAST(
        a.ApproxRevenue
        * 100.0
        / NULLIF(
            t.RevenueTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS AchievementPct,

    CAST(
        a.ApproxRevenue
        - t.RevenueTarget
        AS DECIMAL(19,2)
    ) AS Variance

FROM sales.StoreMonthlyTarget t

INNER JOIN MonthlyActual a
    ON t.StoreId
       = a.StoreId

    AND t.TargetYear
       = a.SalesYear

    AND t.TargetMonth
       = a.SalesMonth

INNER JOIN core.Store s
    ON t.StoreId
       = s.StoreId

ORDER BY
    AchievementPct ASC;
GO


/* =========================================================
   4. COMPANY TARGET ACHIEVEMENT BY YEAR
   ========================================================= */

WITH Actual AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

Returns AS
(
    SELECT
        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            r.ReturnedNetAmount
        ) AS Returns

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    GROUP BY
        YEAR(
            o.OrderDateTime
        )
),

Target AS
(
    SELECT
        TargetYear,

        SUM(
            RevenueTarget
        ) AS RevenueTarget

    FROM sales.StoreMonthlyTarget

    GROUP BY
        TargetYear
)

SELECT
    a.SalesYear,

    CAST(
        a.NetSales
        - COALESCE(
            r.Returns,
            0
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        t.RevenueTarget
        AS DECIMAL(19,2)
    ) AS RevenueTarget,

    CAST(
        (
            a.NetSales
            - COALESCE(
                r.Returns,
                0
            )
        )
        * 100.0
        / NULLIF(
            t.RevenueTarget,
            0
        )
        AS DECIMAL(10,2)
    ) AS AchievementPct

FROM Actual a

LEFT JOIN Returns r
    ON a.SalesYear
       = r.SalesYear

INNER JOIN Target t
    ON a.SalesYear
       = t.TargetYear

ORDER BY
    a.SalesYear;
GO