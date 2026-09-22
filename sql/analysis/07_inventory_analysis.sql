/*
============================================================
 UAE Retail Intelligence Platform
 File: 07_inventory_analysis.sql

 Inventory Analytics

 Includes:
 - Inventory KPI summary
 - Stock status
 - Inventory value
 - Reorder risk
 - Fast / Slow movers
 - Days since last sale
 - Inventory movement analysis
 - Store inventory health
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. INVENTORY KPI SUMMARY
   ========================================================= */

SELECT
    COUNT_BIG(*)
        AS StoreProductCombinations,

    SUM(
        i.CurrentStock
    ) AS StockOnHandUnits,

    CAST(
        SUM(
            i.CurrentStock
            * p.StandardCost
        )
        AS DECIMAL(19,2)
    ) AS InventoryValue,

    SUM(
        CASE
            WHEN i.CurrentStock = 0
                THEN 1
            ELSE 0
        END
    ) AS StockoutSKUs,

    SUM(
        CASE
            WHEN
                i.CurrentStock > 0
                AND i.CurrentStock
                    <= i.ReorderPoint
                THEN 1
            ELSE 0
        END
    ) AS LowStockSKUs,

    SUM(
        CASE
            WHEN
                i.CurrentStock
                > i.ReorderPoint
                THEN 1
            ELSE 0
        END
    ) AS HealthyStockSKUs,

    CAST(
        SUM(
            CASE
                WHEN i.CurrentStock = 0
                    THEN 1.0
                ELSE 0.0
            END
        )
        * 100.0
        / NULLIF(
            COUNT_BIG(*),
            0
        )
        AS DECIMAL(10,2)
    ) AS CurrentStockoutPct

FROM inventory.StoreProductInventory i

INNER JOIN product.Product p
    ON i.ProductId
       = p.ProductId;
GO


/* =========================================================
   2. CURRENT INVENTORY STATUS
   ========================================================= */

SELECT
    i.StoreId,
    s.StoreCode,
    s.StoreName,

    e.EmirateName,

    i.ProductId,
    p.SKU,
    p.ProductName,

    c.CategoryName,

    i.CurrentStock,
    i.ReorderPoint,
    i.ReorderQuantity,

    CAST(
        i.CurrentStock
        * p.StandardCost
        AS DECIMAL(19,2)
    ) AS InventoryValue,

    CASE
        WHEN i.CurrentStock <= 0
            THEN 'STOCKOUT'

        WHEN i.CurrentStock
            <= i.ReorderPoint
            THEN 'LOW_STOCK'

        ELSE 'HEALTHY'
    END AS StockStatus

FROM inventory.StoreProductInventory i

INNER JOIN core.Store s
    ON i.StoreId = s.StoreId

INNER JOIN core.City city
    ON s.CityId = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

INNER JOIN product.Product p
    ON i.ProductId
       = p.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category c
    ON sc.CategoryId
       = c.CategoryId

ORDER BY
    CASE
        WHEN i.CurrentStock <= 0
            THEN 1
        WHEN i.CurrentStock
            <= i.ReorderPoint
            THEN 2
        ELSE 3
    END,
    InventoryValue DESC;
GO


/* =========================================================
   3. REORDER CANDIDATES
   ========================================================= */

SELECT
    s.StoreCode,
    s.StoreName,

    p.SKU,
    p.ProductName,

    c.CategoryName,

    i.CurrentStock,
    i.ReorderPoint,
    i.ReorderQuantity,

    CASE
        WHEN i.CurrentStock = 0
            THEN 'CRITICAL'

        WHEN i.CurrentStock
            <= (
                i.ReorderPoint
                * 0.50
            )
            THEN 'HIGH'

        ELSE 'MEDIUM'
    END AS ReorderRisk,

    i.ReorderQuantity
        AS SuggestedOrderQuantity,

    CAST(
        i.ReorderQuantity
        * p.StandardCost
        AS DECIMAL(19,2)
    ) AS EstimatedReorderCost

FROM inventory.StoreProductInventory i

INNER JOIN core.Store s
    ON i.StoreId = s.StoreId

INNER JOIN product.Product p
    ON i.ProductId = p.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category c
    ON sc.CategoryId
       = c.CategoryId

WHERE
    i.CurrentStock
    <= i.ReorderPoint

ORDER BY
    CASE
        WHEN i.CurrentStock = 0
            THEN 1

        WHEN i.CurrentStock
            <= (
                i.ReorderPoint
                * 0.50
            )
            THEN 2

        ELSE 3
    END,

    EstimatedReorderCost DESC;
GO


/* =========================================================
   4. PRODUCT SALES VELOCITY
   ========================================================= */

WITH ProductSales AS
(
    SELECT
        i.ProductId,

        SUM(
            i.Quantity
        ) AS UnitsSold,

        COUNT(
            DISTINCT CAST(
                o.OrderDateTime
                AS DATE
            )
        ) AS SellingDays,

        MAX(
            o.OrderDateTime
        ) AS LastSaleDate

    FROM sales.SalesOrderItem i

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        i.ProductId
),

Velocity AS
(
    SELECT
        ProductId,
        UnitsSold,
        SellingDays,
        LastSaleDate,

        UnitsSold
        * 1.0
        / NULLIF(
            SellingDays,
            0
        ) AS UnitsPerSellingDay

    FROM ProductSales
),

Ranked AS
(
    SELECT
        *,

        NTILE(4) OVER
        (
            ORDER BY
                UnitsPerSellingDay
        ) AS VelocityQuartile

    FROM Velocity
)

SELECT
    p.SKU,
    p.ProductName,

    c.CategoryName,

    r.UnitsSold,
    r.SellingDays,

    CAST(
        r.UnitsPerSellingDay
        AS DECIMAL(10,2)
    ) AS UnitsPerSellingDay,

    CAST(
        r.LastSaleDate
        AS DATE
    ) AS LastSaleDate,

    DATEDIFF(
        DAY,
        CAST(
            r.LastSaleDate
            AS DATE
        ),
        '2025-12-31'
    ) AS DaysSinceLastSale,

    CASE
        WHEN r.VelocityQuartile = 4
            THEN 'FAST_MOVING'

        WHEN r.VelocityQuartile = 1
            THEN 'SLOW_MOVING'

        ELSE 'NORMAL'
    END AS MovementClass

FROM Ranked r

INNER JOIN product.Product p
    ON r.ProductId
       = p.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category c
    ON sc.CategoryId
       = c.CategoryId

ORDER BY
    r.UnitsPerSellingDay DESC;
GO


/* =========================================================
   5. SLOW-MOVING INVENTORY WITH VALUE AT RISK
   ========================================================= */

WITH ProductSales AS
(
    SELECT
        ProductId,

        SUM(
            Quantity
        ) AS UnitsSold

    FROM sales.SalesOrderItem

    GROUP BY
        ProductId
),

ProductVelocity AS
(
    SELECT
        ProductId,
        UnitsSold,

        NTILE(4) OVER
        (
            ORDER BY UnitsSold
        ) AS VelocityQuartile

    FROM ProductSales
)

SELECT TOP (50)

    p.SKU,
    p.ProductName,

    c.CategoryName,

    SUM(
        i.CurrentStock
    ) AS StockOnHand,

    CAST(
        SUM(
            i.CurrentStock
            * p.StandardCost
        )
        AS DECIMAL(19,2)
    ) AS InventoryValue,

    v.UnitsSold

FROM inventory.StoreProductInventory i

INNER JOIN product.Product p
    ON i.ProductId
       = p.ProductId

INNER JOIN ProductVelocity v
    ON p.ProductId
       = v.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category c
    ON sc.CategoryId
       = c.CategoryId

WHERE
    v.VelocityQuartile = 1

GROUP BY
    p.SKU,
    p.ProductName,
    c.CategoryName,
    v.UnitsSold

ORDER BY
    InventoryValue DESC;
GO


/* =========================================================
   6. INVENTORY MOVEMENT SUMMARY
   ========================================================= */

SELECT
    MovementType,

    COUNT_BIG(*)
        AS Movements,

    SUM(
        ABS(
            QuantityChange
        )
    ) AS UnitsMoved,

    SUM(
        QuantityChange
    ) AS NetQuantityImpact,

    CAST(
        SUM(
            ABS(
                QuantityChange
            )
            * UnitCost
        )
        AS DECIMAL(19,2)
    ) AS MovementValue

FROM inventory.InventoryMovement

GROUP BY
    MovementType

ORDER BY
    Movements DESC;
GO


/* =========================================================
   7. MONTHLY INVENTORY MOVEMENT TREND
   ========================================================= */

SELECT
    DATEFROMPARTS(
        YEAR(
            MovementDateTime
        ),
        MONTH(
            MovementDateTime
        ),
        1
    ) AS MonthStart,

    MovementType,

    COUNT_BIG(*)
        AS Movements,

    SUM(
        QuantityChange
    ) AS NetQuantityChange,

    SUM(
        ABS(
            QuantityChange
        )
    ) AS AbsoluteUnitsMoved

FROM inventory.InventoryMovement

GROUP BY
    DATEFROMPARTS(
        YEAR(
            MovementDateTime
        ),
        MONTH(
            MovementDateTime
        ),
        1
    ),
    MovementType

ORDER BY
    MonthStart,
    MovementType;
GO


/* =========================================================
   8. INVENTORY HEALTH BY STORE
   ========================================================= */

SELECT
    s.StoreCode,
    s.StoreName,

    e.EmirateName,

    COUNT_BIG(*)
        AS ProductSKUs,

    SUM(
        i.CurrentStock
    ) AS StockUnits,

    CAST(
        SUM(
            i.CurrentStock
            * p.StandardCost
        )
        AS DECIMAL(19,2)
    ) AS InventoryValue,

    SUM(
        CASE
            WHEN i.CurrentStock = 0
                THEN 1
            ELSE 0
        END
    ) AS StockoutSKUs,

    SUM(
        CASE
            WHEN
                i.CurrentStock > 0
                AND i.CurrentStock
                    <= i.ReorderPoint
                THEN 1
            ELSE 0
        END
    ) AS LowStockSKUs,

    CAST(
        SUM(
            CASE
                WHEN
                    i.CurrentStock
                    <= i.ReorderPoint
                    THEN 1.0
                ELSE 0.0
            END
        )
        * 100.0
        / NULLIF(
            COUNT_BIG(*),
            0
        )
        AS DECIMAL(10,2)
    ) AS ReorderRiskPct

FROM inventory.StoreProductInventory i

INNER JOIN core.Store s
    ON i.StoreId = s.StoreId

INNER JOIN core.City city
    ON s.CityId = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

INNER JOIN product.Product p
    ON i.ProductId
       = p.ProductId

GROUP BY
    s.StoreCode,
    s.StoreName,
    e.EmirateName

ORDER BY
    ReorderRiskPct DESC;
GO