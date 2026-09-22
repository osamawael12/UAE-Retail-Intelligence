/*
============================================================
 UAE Retail Intelligence Platform
 File: 04_inventory_targets_views.sql

 Views:
 - analytics.vw_InventoryStatus
 - analytics.vw_TargetPerformance
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   INVENTORY STATUS

   Grain:
   Store x Product
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_InventoryStatus
AS

WITH ProductSales AS
(
    SELECT
        o.StoreId,
        i.ProductId,

        SUM(
            i.Quantity
        ) AS GrossUnitsSold,

        MAX(
            o.OrderDateTime
        ) AS LastSaleDate

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        o.StoreId,
        i.ProductId
)

SELECT
    inv.StoreId,
    s.StoreCode,
    s.StoreName,

    e.EmirateId,
    e.EmirateName,

    inv.ProductId,
    p.SKU,
    p.ProductName,

    cat.CategoryId,
    cat.CategoryName,

    sc.SubcategoryId,
    sc.SubcategoryName,

    b.BrandId,
    b.BrandName,

    inv.CurrentStock,
    inv.ReorderPoint,
    inv.ReorderQuantity,

    p.StandardCost,

    inv.CurrentStock
        * p.StandardCost
        AS InventoryValue,

    COALESCE(
        ps.GrossUnitsSold,
        0
    ) AS GrossUnitsSold,

    ps.LastSaleDate,

    CASE
        WHEN
            ps.LastSaleDate
            IS NULL
            THEN NULL

        ELSE
            DATEDIFF(
                DAY,
                CAST(
                    ps.LastSaleDate
                    AS DATE
                ),
                '2025-12-31'
            )
    END AS DaysSinceLastSale,

    CASE
        WHEN
            inv.CurrentStock <= 0
            THEN 'STOCKOUT'

        WHEN
            inv.CurrentStock
            <= inv.ReorderPoint
            THEN 'LOW_STOCK'

        ELSE 'HEALTHY'
    END AS StockStatus,

    CASE
        WHEN
            inv.CurrentStock <= 0
            THEN 'CRITICAL'

        WHEN
            inv.CurrentStock
            <= (
                inv.ReorderPoint
                * 0.50
            )
            THEN 'HIGH'

        WHEN
            inv.CurrentStock
            <= inv.ReorderPoint
            THEN 'MEDIUM'

        ELSE 'LOW'
    END AS ReorderRisk

FROM inventory.StoreProductInventory inv

INNER JOIN core.Store s
    ON inv.StoreId
       = s.StoreId

INNER JOIN core.City city
    ON s.CityId
       = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

INNER JOIN product.Product p
    ON inv.ProductId
       = p.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category cat
    ON sc.CategoryId
       = cat.CategoryId

INNER JOIN product.Brand b
    ON p.BrandId
       = b.BrandId

LEFT JOIN ProductSales ps
    ON inv.StoreId
       = ps.StoreId

    AND inv.ProductId
       = ps.ProductId;
GO


/* =========================================================
   TARGET PERFORMANCE

   Grain:
   Store x Month

   Returns are attributed to original sale month to remain
   consistent with the target-generation methodology.
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_TargetPerformance
AS

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
    t.StoreMonthlyTargetId,

    t.StoreId,
    s.StoreCode,
    s.StoreName,

    e.EmirateId,
    e.EmirateName,

    t.TargetYear,
    t.TargetMonth,

    DATEFROMPARTS(
        t.TargetYear,
        t.TargetMonth,
        1
    ) AS MonthStart,

    COALESCE(
        a.Revenue,
        0
    ) AS ActualRevenue,

    t.RevenueTarget,

    COALESCE(
        a.Revenue,
        0
    )
    - t.RevenueTarget
        AS RevenueVariance,

    CASE
        WHEN
            t.RevenueTarget = 0
            THEN NULL

        ELSE
            CAST(
                COALESCE(
                    a.Revenue,
                    0
                )
                * 100.0
                / t.RevenueTarget
                AS DECIMAL(19,6)
            )
    END AS RevenueAchievementPct,

    COALESCE(
        a.GrossProfit,
        0
    ) AS ActualGrossProfit,

    t.GrossProfitTarget,

    COALESCE(
        a.GrossProfit,
        0
    )
    - t.GrossProfitTarget
        AS ProfitVariance,

    CASE
        WHEN
            t.GrossProfitTarget = 0
            THEN NULL

        ELSE
            CAST(
                COALESCE(
                    a.GrossProfit,
                    0
                )
                * 100.0
                / t.GrossProfitTarget
                AS DECIMAL(19,6)
            )
    END AS ProfitAchievementPct,

    COALESCE(
        a.Orders,
        0
    ) AS ActualOrders,

    t.OrdersTarget,

    COALESCE(
        a.Orders,
        0
    )
    - t.OrdersTarget
        AS OrdersVariance,

    CASE
        WHEN
            t.OrdersTarget = 0
            THEN NULL

        ELSE
            CAST(
                COALESCE(
                    a.Orders,
                    0
                )
                * 100.0
                / t.OrdersTarget
                AS DECIMAL(19,6)
            )
    END AS OrdersAchievementPct

FROM sales.StoreMonthlyTarget t

INNER JOIN core.Store s
    ON t.StoreId
       = s.StoreId

INNER JOIN core.City city
    ON s.CityId
       = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

LEFT JOIN Actuals a
    ON t.StoreId
       = a.StoreId

    AND t.TargetYear
       = a.SalesYear

    AND t.TargetMonth
       = a.SalesMonth;
GO