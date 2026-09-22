/*
============================================================
 UAE Retail Intelligence Platform
 File: 03_store_analysis.sql

 Store & Emirate Analytics

 Includes:
 - Emirate Performance
 - Store Performance
 - Revenue Contribution
 - Gross Profit / Margin
 - Orders / Customers / AOV
 - Return Rate
 - Company Store Ranking
 - Ranking inside Emirate
 - Store YoY Growth
 - Top / Bottom Stores
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. EMIRATE PERFORMANCE
   ========================================================= */

WITH Sales AS
(
    SELECT
        e.EmirateId,
        e.EmirateName,

        SUM(i.NetAmount)
            AS NetSales,

        SUM(i.LineCOGS)
            AS SalesCOGS,

        SUM(i.Quantity)
            AS GrossUnits,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        COUNT_BIG(
            DISTINCT o.CustomerId
        ) AS Customers

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    INNER JOIN core.Store s
        ON o.StoreId = s.StoreId

    INNER JOIN core.City c
        ON s.CityId = c.CityId

    INNER JOIN core.Emirate e
        ON c.EmirateId = e.EmirateId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        e.EmirateId,
        e.EmirateName
),

Returns AS
(
    SELECT
        e.EmirateId,

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
        ON oi.OrderId = o.OrderId

    INNER JOIN core.Store s
        ON o.StoreId = s.StoreId

    INNER JOIN core.City c
        ON s.CityId = c.CityId

    INNER JOIN core.Emirate e
        ON c.EmirateId = e.EmirateId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        e.EmirateId
),

Metrics AS
(
    SELECT
        s.EmirateId,
        s.EmirateName,

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

        s.Orders,
        s.Customers,
        s.GrossUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits

    FROM Sales s

    LEFT JOIN Returns r
        ON s.EmirateId
           = r.EmirateId
),

Final AS
(
    SELECT
        *,

        SUM(
            Revenue
        ) OVER ()
            AS CompanyRevenue

    FROM Metrics
)

SELECT
    EmirateName,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        Revenue
        * 100.0
        / NULLIF(
            CompanyRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenueContributionPct,

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

    RANK() OVER
    (
        ORDER BY Revenue DESC
    ) AS RevenueRank

FROM Final

ORDER BY RevenueRank;
GO


/* =========================================================
   2. STORE PERFORMANCE
   ========================================================= */

WITH StoreSales AS
(
    SELECT
        s.StoreId,
        s.StoreCode,
        s.StoreName,

        e.EmirateName,

        SUM(i.NetAmount)
            AS NetSales,

        SUM(i.LineCOGS)
            AS SalesCOGS,

        SUM(i.Quantity)
            AS GrossUnits,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        COUNT_BIG(
            DISTINCT o.CustomerId
        ) AS Customers

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    INNER JOIN core.Store s
        ON o.StoreId = s.StoreId

    INNER JOIN core.City c
        ON s.CityId = c.CityId

    INNER JOIN core.Emirate e
        ON c.EmirateId = e.EmirateId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        s.StoreId,
        s.StoreCode,
        s.StoreName,
        e.EmirateName
),

StoreReturns AS
(
    SELECT
        o.StoreId,

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
        ON oi.OrderId = o.OrderId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        o.StoreId
),

StoreMetrics AS
(
    SELECT
        s.StoreId,
        s.StoreCode,
        s.StoreName,
        s.EmirateName,

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

        s.Orders,
        s.Customers,
        s.GrossUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits

    FROM StoreSales s

    LEFT JOIN StoreReturns r
        ON s.StoreId = r.StoreId
),

Ranked AS
(
    SELECT
        *,

        SUM(
            Revenue
        ) OVER ()
            AS CompanyRevenue,

        RANK() OVER
        (
            ORDER BY Revenue DESC
        ) AS CompanyRevenueRank,

        RANK() OVER
        (
            PARTITION BY EmirateName
            ORDER BY Revenue DESC
        ) AS EmirateRevenueRank,

        RANK() OVER
        (
            ORDER BY GrossProfit DESC
        ) AS ProfitRank

    FROM StoreMetrics
)

SELECT
    StoreId,
    StoreCode,
    StoreName,
    EmirateName,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        Revenue
        * 100.0
        / NULLIF(
            CompanyRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS CompanyRevenueContributionPct,

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

    CAST(
        Revenue
        / NULLIF(
            Orders,
            0
        )
        AS DECIMAL(19,2)
    ) AS AOV,

    GrossUnits
        - ReturnedUnits
        AS NetUnits,

    CAST(
        ReturnedUnits
        * 100.0
        / NULLIF(
            GrossUnits,
            0
        )
        AS DECIMAL(10,2)
    ) AS ReturnRatePct,

    CompanyRevenueRank,
    EmirateRevenueRank,
    ProfitRank

FROM Ranked

ORDER BY
    CompanyRevenueRank;
GO


/* =========================================================
   3. STORE YEAR-OVER-YEAR GROWTH
   ========================================================= */

WITH Sales AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

Returns AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

    INNER JOIN sales.SalesOrderItem i
        ON ri.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

AnnualRevenue AS
(
    SELECT
        s.StoreId,
        s.SalesYear,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Revenue

    FROM Sales s

    LEFT JOIN Returns r
        ON s.StoreId
           = r.StoreId

        AND s.SalesYear
           = r.SalesYear
),

Growth AS
(
    SELECT
        StoreId,
        SalesYear,
        Revenue,

        LAG(
            Revenue
        ) OVER
        (
            PARTITION BY StoreId
            ORDER BY SalesYear
        ) AS PreviousYearRevenue

    FROM AnnualRevenue
)

SELECT
    g.StoreId,
    s.StoreCode,
    s.StoreName,
    e.EmirateName,

    g.SalesYear,

    CAST(
        g.Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        g.PreviousYearRevenue
        AS DECIMAL(19,2)
    ) AS PreviousYearRevenue,

    CAST(
        (
            g.Revenue
            - g.PreviousYearRevenue
        )
        * 100.0
        / NULLIF(
            g.PreviousYearRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS YoYGrowthPct

FROM Growth g

INNER JOIN core.Store s
    ON g.StoreId = s.StoreId

INNER JOIN core.City c
    ON s.CityId = c.CityId

INNER JOIN core.Emirate e
    ON c.EmirateId = e.EmirateId

ORDER BY
    g.SalesYear,
    YoYGrowthPct DESC;
GO


/* =========================================================
   4. TOP 5 STORES PER YEAR
   ========================================================= */

WITH AnnualSales AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

AnnualReturns AS
(
    SELECT
        o.StoreId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        SUM(
            ri.ReturnedNetAmount
        ) AS Returns

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

    INNER JOIN sales.SalesOrderItem i
        ON ri.OrderItemId = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        o.StoreId,
        YEAR(
            o.OrderDateTime
        )
),

Revenue AS
(
    SELECT
        a.StoreId,
        a.SalesYear,

        a.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue

    FROM AnnualSales a

    LEFT JOIN AnnualReturns r
        ON a.StoreId = r.StoreId

        AND a.SalesYear
            = r.SalesYear
),

Ranked AS
(
    SELECT
        *,

        ROW_NUMBER() OVER
        (
            PARTITION BY SalesYear
            ORDER BY Revenue DESC
        ) AS StoreRank

    FROM Revenue
)

SELECT
    r.SalesYear,
    r.StoreRank,

    s.StoreCode,
    s.StoreName,

    e.EmirateName,

    CAST(
        r.Revenue
        AS DECIMAL(19,2)
    ) AS Revenue

FROM Ranked r

INNER JOIN core.Store s
    ON r.StoreId = s.StoreId

INNER JOIN core.City c
    ON s.CityId = c.CityId

INNER JOIN core.Emirate e
    ON c.EmirateId = e.EmirateId

WHERE
    r.StoreRank <= 5

ORDER BY
    r.SalesYear,
    r.StoreRank;
GO


/* =========================================================
   5. BOTTOM 5 STORES BY REVENUE
   ========================================================= */

WITH StoreRevenue AS
(
    SELECT
        o.StoreId,

        SUM(
            i.NetAmount
        )
        -
        COALESCE(
            (
                SELECT
                    SUM(
                        ri.ReturnedNetAmount
                    )

                FROM sales.ReturnItem ri

                INNER JOIN sales.[Return] r
                    ON ri.ReturnId
                       = r.ReturnId

                INNER JOIN sales.SalesOrderItem oi
                    ON ri.OrderItemId
                       = oi.OrderItemId

                INNER JOIN sales.SalesOrder ro
                    ON oi.OrderId
                       = ro.OrderId

                WHERE
                    ro.StoreId
                    = o.StoreId

                    AND r.ReturnStatus
                        = 'COMPLETED'
            ),
            0
        ) AS Revenue

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        o.StoreId
),

Ranked AS
(
    SELECT
        *,

        ROW_NUMBER() OVER
        (
            ORDER BY Revenue ASC
        ) AS BottomRank

    FROM StoreRevenue
)

SELECT
    r.BottomRank,

    s.StoreCode,
    s.StoreName,

    e.EmirateName,

    CAST(
        r.Revenue
        AS DECIMAL(19,2)
    ) AS Revenue

FROM Ranked r

INNER JOIN core.Store s
    ON r.StoreId = s.StoreId

INNER JOIN core.City c
    ON s.CityId = c.CityId

INNER JOIN core.Emirate e
    ON c.EmirateId = e.EmirateId

WHERE
    r.BottomRank <= 5

ORDER BY
    r.BottomRank;
GO