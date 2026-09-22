/*
============================================================
 UAE Retail Intelligence Platform
 File: 11_pareto_abc_analysis.sql

 Product Pareto & ABC Analysis

 Includes:
 - Product Revenue
 - Revenue Contribution
 - Cumulative Revenue
 - Cumulative Revenue %
 - ABC Classification
 - Products responsible for ~80% of revenue
 - Category concentration
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. PRODUCT PARETO ANALYSIS
   ========================================================= */

WITH ProductSales AS
(
    SELECT
        p.ProductId,
        p.SKU,
        p.ProductName,

        c.CategoryName,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrderItem i

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    INNER JOIN product.Product p
        ON i.ProductId
           = p.ProductId

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        p.ProductId,
        p.SKU,
        p.ProductName,
        c.CategoryName
),

ProductReturns AS
(
    SELECT
        i.ProductId,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    INNER JOIN sales.SalesOrderItem i
        ON ri.OrderItemId
           = i.OrderItemId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        i.ProductId
),

ProductRevenue AS
(
    SELECT
        s.ProductId,
        s.SKU,
        s.ProductName,
        s.CategoryName,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Revenue

    FROM ProductSales s

    LEFT JOIN ProductReturns r
        ON s.ProductId
           = r.ProductId
),

Ranked AS
(
    SELECT
        *,

        SUM(
            Revenue
        ) OVER ()
            AS TotalRevenue,

        SUM(
            Revenue
        ) OVER
        (
            ORDER BY
                Revenue DESC,
                ProductId

            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS CumulativeRevenue,

        ROW_NUMBER() OVER
        (
            ORDER BY
                Revenue DESC,
                ProductId
        ) AS ProductRank,

        COUNT(*) OVER ()
            AS TotalProducts

    FROM ProductRevenue
),

Metrics AS
(
    SELECT
        *,

        Revenue
        * 100.0
        / NULLIF(
            TotalRevenue,
            0
        ) AS RevenueContributionPct,

        CumulativeRevenue
        * 100.0
        / NULLIF(
            TotalRevenue,
            0
        ) AS CumulativeRevenuePct,

        ProductRank
        * 100.0
        / NULLIF(
            TotalProducts,
            0
        ) AS CumulativeProductPct

    FROM Ranked
)

SELECT
    ProductRank,

    SKU,
    ProductName,
    CategoryName,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        RevenueContributionPct
        AS DECIMAL(10,4)
    ) AS RevenueContributionPct,

    CAST(
        CumulativeRevenue
        AS DECIMAL(19,2)
    ) AS CumulativeRevenue,

    CAST(
        CumulativeRevenuePct
        AS DECIMAL(10,2)
    ) AS CumulativeRevenuePct,

    CAST(
        CumulativeProductPct
        AS DECIMAL(10,2)
    ) AS CumulativeProductPct,

    CASE
        WHEN
            CumulativeRevenuePct
            <= 80
            THEN 'A'

        WHEN
            CumulativeRevenuePct
            <= 95
            THEN 'B'

        ELSE 'C'
    END AS ABCClass

FROM Metrics

ORDER BY
    ProductRank;
GO


/* =========================================================
   2. ABC CLASS SUMMARY
   ========================================================= */

WITH ProductSales AS
(
    SELECT
        ProductId,

        SUM(
            NetAmount
        ) AS NetSales

    FROM sales.SalesOrderItem

    GROUP BY ProductId
),

ProductReturns AS
(
    SELECT
        i.ProductId,

        SUM(
            r.ReturnedNetAmount
        ) AS Returns

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    GROUP BY
        i.ProductId
),

Revenue AS
(
    SELECT
        s.ProductId,

        s.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue

    FROM ProductSales s

    LEFT JOIN ProductReturns r
        ON s.ProductId
           = r.ProductId
),

Running AS
(
    SELECT
        ProductId,
        Revenue,

        SUM(
            Revenue
        ) OVER ()
            AS TotalRevenue,

        SUM(
            Revenue
        ) OVER
        (
            ORDER BY
                Revenue DESC,
                ProductId

            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS CumulativeRevenue

    FROM Revenue
),

Classified AS
(
    SELECT
        *,

        CASE
            WHEN
                CumulativeRevenue
                * 100.0
                / NULLIF(
                    TotalRevenue,
                    0
                )
                <= 80
                THEN 'A'

            WHEN
                CumulativeRevenue
                * 100.0
                / NULLIF(
                    TotalRevenue,
                    0
                )
                <= 95
                THEN 'B'

            ELSE 'C'
        END AS ABCClass

    FROM Running
)

SELECT
    ABCClass,

    COUNT_BIG(*)
        AS Products,

    CAST(
        COUNT_BIG(*)
        * 100.0
        /
        SUM(
            COUNT_BIG(*)
        ) OVER ()
        AS DECIMAL(10,2)
    ) AS ProductPct,

    CAST(
        SUM(
            Revenue
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        SUM(
            Revenue
        )
        * 100.0
        /
        NULLIF(
            SUM(
                SUM(
                    Revenue
                )
            ) OVER (),
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenuePct

FROM Classified

GROUP BY
    ABCClass

ORDER BY
    ABCClass;
GO


/* =========================================================
   3. HOW MANY PRODUCTS GENERATE ~80% OF REVENUE?
   ========================================================= */

WITH Revenue AS
(
    SELECT
        ProductId,

        SUM(
            NetAmount
        ) AS Revenue

    FROM sales.SalesOrderItem

    GROUP BY
        ProductId
),

Running AS
(
    SELECT
        ProductId,
        Revenue,

        SUM(
            Revenue
        ) OVER ()
            AS TotalRevenue,

        SUM(
            Revenue
        ) OVER
        (
            ORDER BY
                Revenue DESC,
                ProductId

            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS CumulativeRevenue,

        ROW_NUMBER() OVER
        (
            ORDER BY
                Revenue DESC,
                ProductId
        ) AS ProductRank,

        COUNT(*) OVER ()
            AS TotalProducts

    FROM Revenue
),

Boundary AS
(
    SELECT TOP (1)
        ProductRank,
        TotalProducts,

        CumulativeRevenue,
        TotalRevenue

    FROM Running

    WHERE
        CumulativeRevenue
        >= TotalRevenue * 0.80

    ORDER BY
        ProductRank
)

SELECT
    ProductRank
        AS ProductsNeededFor80PctRevenue,

    TotalProducts,

    CAST(
        ProductRank
        * 100.0
        / NULLIF(
            TotalProducts,
            0
        )
        AS DECIMAL(10,2)
    ) AS ProductPctNeeded,

    CAST(
        CumulativeRevenue
        * 100.0
        / NULLIF(
            TotalRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS ActualCumulativeRevenuePct

FROM Boundary;
GO


/* =========================================================
   4. CATEGORY REVENUE CONCENTRATION
   ========================================================= */

WITH CategoryRevenue AS
(
    SELECT
        c.CategoryName,

        SUM(
            i.NetAmount
        ) AS Revenue

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

    GROUP BY
        c.CategoryName
),

Ranked AS
(
    SELECT
        *,

        SUM(
            Revenue
        ) OVER ()
            AS TotalRevenue,

        SUM(
            Revenue
        ) OVER
        (
            ORDER BY Revenue DESC

            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS CumulativeRevenue

    FROM CategoryRevenue
)

SELECT
    CategoryName,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        Revenue
        * 100.0
        / NULLIF(
            TotalRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenuePct,

    CAST(
        CumulativeRevenue
        * 100.0
        / NULLIF(
            TotalRevenue,
            0
        )
        AS DECIMAL(10,2)
    ) AS CumulativeRevenuePct

FROM Ranked

ORDER BY
    Revenue DESC;
GO