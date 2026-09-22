/*
============================================================
 UAE Retail Intelligence Platform
 File: 12_basket_analysis.sql

 Market Basket Analysis

 Includes:
 - Basket size
 - Product pairs
 - Pair support
 - Category pairs
 - Cross-sell opportunities

 Product pairing rule:
 ProductId1 < ProductId2

 This avoids duplicate pairs:
 A + B
 B + A
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. BASKET SIZE SUMMARY
   ========================================================= */

WITH Basket AS
(
    SELECT
        OrderId,

        COUNT_BIG(*)
            AS ProductLines,

        SUM(
            Quantity
        ) AS Units,

        SUM(
            NetAmount
        ) AS BasketNetSales

    FROM sales.SalesOrderItem

    GROUP BY
        OrderId
)

SELECT
    COUNT_BIG(*)
        AS Orders,

    CAST(
        AVG(
            CAST(
                ProductLines
                AS DECIMAL(19,4)
            )
        )
        AS DECIMAL(10,2)
    ) AS AvgProductLinesPerOrder,

    CAST(
        AVG(
            CAST(
                Units
                AS DECIMAL(19,4)
            )
        )
        AS DECIMAL(10,2)
    ) AS AvgUnitsPerOrder,

    CAST(
        AVG(
            BasketNetSales
        )
        AS DECIMAL(19,2)
    ) AS AvgBasketNetSales,

    MAX(
        ProductLines
    ) AS MaxProductLines,

    MAX(
        Units
    ) AS MaxUnits

FROM Basket;
GO


/* =========================================================
   2. BASKET SIZE DISTRIBUTION
   ========================================================= */

WITH Basket AS
(
    SELECT
        OrderId,

        COUNT_BIG(*)
            AS ProductLines

    FROM sales.SalesOrderItem

    GROUP BY
        OrderId
),

Bands AS
(
    SELECT
        CASE
            WHEN ProductLines = 1
                THEN '1 Product'

            WHEN ProductLines = 2
                THEN '2 Products'

            WHEN ProductLines = 3
                THEN '3 Products'

            WHEN ProductLines BETWEEN 4 AND 5
                THEN '4-5 Products'

            ELSE '6+ Products'
        END AS BasketBand

    FROM Basket
)

SELECT
    BasketBand,

    COUNT_BIG(*)
        AS Orders,

    CAST(
        COUNT_BIG(*)
        * 100.0
        /
        SUM(
            COUNT_BIG(*)
        ) OVER ()
        AS DECIMAL(10,2)
    ) AS OrderPct

FROM Bands

GROUP BY
    BasketBand

ORDER BY
    CASE BasketBand
        WHEN '1 Product'
            THEN 1
        WHEN '2 Products'
            THEN 2
        WHEN '3 Products'
            THEN 3
        WHEN '4-5 Products'
            THEN 4
        ELSE 5
    END;
GO


/* =========================================================
   3. MOST FREQUENT PRODUCT PAIRS
   ========================================================= */

WITH OrderProducts AS
(
    SELECT DISTINCT
        OrderId,
        ProductId

    FROM sales.SalesOrderItem
),

Pairs AS
(
    SELECT
        a.OrderId,

        a.ProductId
            AS ProductId1,

        b.ProductId
            AS ProductId2

    FROM OrderProducts a

    INNER JOIN OrderProducts b
        ON a.OrderId
           = b.OrderId

        AND a.ProductId
            < b.ProductId
),

PairCounts AS
(
    SELECT
        ProductId1,
        ProductId2,

        COUNT_BIG(*)
            AS PairOrders

    FROM Pairs

    GROUP BY
        ProductId1,
        ProductId2
)

SELECT TOP (30)

    p1.SKU
        AS SKU1,

    p1.ProductName
        AS Product1,

    p2.SKU
        AS SKU2,

    p2.ProductName
        AS Product2,

    pc.PairOrders

FROM PairCounts pc

INNER JOIN product.Product p1
    ON pc.ProductId1
       = p1.ProductId

INNER JOIN product.Product p2
    ON pc.ProductId2
       = p2.ProductId

ORDER BY
    pc.PairOrders DESC,
    SKU1,
    SKU2;
GO


/* =========================================================
   4. PRODUCT PAIR SUPPORT

   Support =
   Orders containing both products / Total Orders
   ========================================================= */

WITH TotalOrders AS
(
    SELECT
        COUNT_BIG(*)
            AS TotalOrders

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'
),

OrderProducts AS
(
    SELECT DISTINCT
        i.OrderId,
        i.ProductId

    FROM sales.SalesOrderItem i

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'
),

Pairs AS
(
    SELECT
        a.ProductId
            AS ProductId1,

        b.ProductId
            AS ProductId2,

        COUNT_BIG(*)
            AS PairOrders

    FROM OrderProducts a

    INNER JOIN OrderProducts b
        ON a.OrderId
           = b.OrderId

        AND a.ProductId
            < b.ProductId

    GROUP BY
        a.ProductId,
        b.ProductId
)

SELECT TOP (30)

    p1.SKU AS SKU1,
    p1.ProductName AS Product1,

    p2.SKU AS SKU2,
    p2.ProductName AS Product2,

    pair.PairOrders,

    CAST(
        pair.PairOrders
        * 100.0
        / NULLIF(
            total.TotalOrders,
            0
        )
        AS DECIMAL(10,4)
    ) AS SupportPct

FROM Pairs pair

CROSS JOIN TotalOrders total

INNER JOIN product.Product p1
    ON pair.ProductId1
       = p1.ProductId

INNER JOIN product.Product p2
    ON pair.ProductId2
       = p2.ProductId

ORDER BY
    SupportPct DESC,
    pair.PairOrders DESC;
GO


/* =========================================================
   5. CATEGORY PAIRS

   More stable than individual product pairs because there
   are 800 products but only 8 categories.
   ========================================================= */

WITH OrderCategories AS
(
    SELECT DISTINCT
        i.OrderId,
        c.CategoryId,
        c.CategoryName

    FROM sales.SalesOrderItem i

    INNER JOIN product.Product p
        ON i.ProductId
           = p.ProductId

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId
),

Pairs AS
(
    SELECT
        a.CategoryId
            AS CategoryId1,

        a.CategoryName
            AS Category1,

        b.CategoryId
            AS CategoryId2,

        b.CategoryName
            AS Category2,

        COUNT_BIG(*)
            AS OrdersTogether

    FROM OrderCategories a

    INNER JOIN OrderCategories b
        ON a.OrderId
           = b.OrderId

        AND a.CategoryId
            < b.CategoryId

    GROUP BY
        a.CategoryId,
        a.CategoryName,
        b.CategoryId,
        b.CategoryName
)

SELECT
    Category1,
    Category2,

    OrdersTogether,

    RANK() OVER
    (
        ORDER BY
            OrdersTogether DESC
    ) AS PairRank

FROM Pairs

ORDER BY
    PairRank;
GO


/* =========================================================
   6. BASIC CROSS-SELL OPPORTUNITY

   For each product pair:
   - PairOrders
   - Orders containing Product A
   - Orders containing Product B

   Confidence A -> B =
   PairOrders / Orders containing A

   Confidence B -> A =
   PairOrders / Orders containing B
   ========================================================= */

WITH OrderProducts AS
(
    SELECT DISTINCT
        OrderId,
        ProductId

    FROM sales.SalesOrderItem
),

ProductOrders AS
(
    SELECT
        ProductId,

        COUNT_BIG(*)
            AS ProductOrders

    FROM OrderProducts

    GROUP BY
        ProductId
),

PairOrders AS
(
    SELECT
        a.ProductId
            AS ProductId1,

        b.ProductId
            AS ProductId2,

        COUNT_BIG(*)
            AS PairOrders

    FROM OrderProducts a

    INNER JOIN OrderProducts b
        ON a.OrderId
           = b.OrderId

        AND a.ProductId
            < b.ProductId

    GROUP BY
        a.ProductId,
        b.ProductId
),

Metrics AS
(
    SELECT
        pair.ProductId1,
        pair.ProductId2,
        pair.PairOrders,

        p1.ProductOrders
            AS Product1Orders,

        p2.ProductOrders
            AS Product2Orders,

        pair.PairOrders
        * 1.0
        / NULLIF(
            p1.ProductOrders,
            0
        ) AS Confidence1To2,

        pair.PairOrders
        * 1.0
        / NULLIF(
            p2.ProductOrders,
            0
        ) AS Confidence2To1

    FROM PairOrders pair

    INNER JOIN ProductOrders p1
        ON pair.ProductId1
           = p1.ProductId

    INNER JOIN ProductOrders p2
        ON pair.ProductId2
           = p2.ProductId
)

SELECT TOP (30)

    p1.SKU AS SKU1,
    p1.ProductName AS Product1,

    p2.SKU AS SKU2,
    p2.ProductName AS Product2,

    m.PairOrders,

    CAST(
        m.Confidence1To2
        * 100
        AS DECIMAL(10,2)
    ) AS Confidence1To2Pct,

    CAST(
        m.Confidence2To1
        * 100
        AS DECIMAL(10,2)
    ) AS Confidence2To1Pct

FROM Metrics m

INNER JOIN product.Product p1
    ON m.ProductId1
       = p1.ProductId

INNER JOIN product.Product p2
    ON m.ProductId2
       = p2.ProductId

WHERE
    m.PairOrders >= 3

ORDER BY
    m.PairOrders DESC,
    Confidence1To2Pct DESC;
GO