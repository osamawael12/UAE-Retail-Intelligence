/*
============================================================
 UAE Retail Intelligence Platform
 File: 04_product_analysis.sql

 Product Analytics

 Includes:
 - Category Performance
 - Product Performance
 - Profitability
 - Return Rate
 - Discount Dependency
 - Top Products per Category
 - Bottom Products
 - Brand Performance
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. CATEGORY PERFORMANCE
   ========================================================= */

WITH Sales AS
(
    SELECT
        c.CategoryId,
        c.CategoryName,

        SUM(i.NetAmount)
            AS NetSales,

        SUM(i.LineCOGS)
            AS SalesCOGS,

        SUM(i.Quantity)
            AS GrossUnits,

        SUM(i.DiscountAmount)
            AS DiscountAmount

    FROM sales.SalesOrderItem i

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        c.CategoryId,
        c.CategoryName
),

Returns AS
(
    SELECT
        c.CategoryId,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits,

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

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        c.CategoryId
),

Metrics AS
(
    SELECT
        s.CategoryName,

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

        s.GrossUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits,

        s.DiscountAmount

    FROM Sales s

    LEFT JOIN Returns r
        ON s.CategoryId
           = r.CategoryId
)

SELECT
    CategoryName,

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

    CAST(
        DiscountAmount
        AS DECIMAL(19,2)
    ) AS DiscountAmount,

    RANK() OVER
    (
        ORDER BY Revenue DESC
    ) AS RevenueRank,

    RANK() OVER
    (
        ORDER BY GrossProfit DESC
    ) AS ProfitRank

FROM Metrics

ORDER BY RevenueRank;
GO


/* =========================================================
   2. PRODUCT PERFORMANCE
   ========================================================= */

WITH ProductSales AS
(
    SELECT
        p.ProductId,
        p.SKU,
        p.ProductName,

        c.CategoryName,
        sc.SubcategoryName,
        b.BrandName,

        SUM(i.NetAmount)
            AS NetSales,

        SUM(i.LineCOGS)
            AS SalesCOGS,

        SUM(i.Quantity)
            AS GrossUnits,

        SUM(i.DiscountAmount)
            AS DiscountAmount,

        SUM(
            CASE
                WHEN i.DiscountAmount > 0
                    THEN i.NetAmount
                ELSE 0
            END
        ) AS DiscountedNetSales

    FROM sales.SalesOrderItem i

    INNER JOIN sales.SalesOrder o
        ON i.OrderId = o.OrderId

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId

    INNER JOIN product.Brand b
        ON p.BrandId = b.BrandId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        p.ProductId,
        p.SKU,
        p.ProductName,
        c.CategoryName,
        sc.SubcategoryName,
        b.BrandName
),

ProductReturns AS
(
    SELECT
        i.ProductId,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits,

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

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        i.ProductId
),

Metrics AS
(
    SELECT
        s.*,

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

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits

    FROM ProductSales s

    LEFT JOIN ProductReturns r
        ON s.ProductId
           = r.ProductId
)

SELECT
    ProductId,
    SKU,
    ProductName,

    CategoryName,
    SubcategoryName,
    BrandName,

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

    CAST(
        DiscountedNetSales
        * 100.0
        / NULLIF(
            NetSales,
            0
        )
        AS DECIMAL(10,2)
    ) AS DiscountDependencyPct,

    RANK() OVER
    (
        ORDER BY Revenue DESC
    ) AS RevenueRank,

    RANK() OVER
    (
        ORDER BY GrossProfit DESC
    ) AS ProfitRank

FROM Metrics

ORDER BY RevenueRank;
GO


/* =========================================================
   3. TOP 5 PRODUCTS PER CATEGORY
   ========================================================= */

WITH ProductRevenue AS
(
    SELECT
        c.CategoryName,

        p.ProductId,
        p.SKU,
        p.ProductName,

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

                INNER JOIN sales.SalesOrderItem ri_item
                    ON ri.OrderItemId
                       = ri_item.OrderItemId

                WHERE
                    ri_item.ProductId
                    = p.ProductId

                    AND r.ReturnStatus
                    = 'COMPLETED'
            ),
            0
        ) AS Revenue

    FROM product.Product p

    INNER JOIN product.Subcategory sc
        ON p.SubcategoryId
           = sc.SubcategoryId

    INNER JOIN product.Category c
        ON sc.CategoryId
           = c.CategoryId

    INNER JOIN sales.SalesOrderItem i
        ON p.ProductId
           = i.ProductId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        c.CategoryName,
        p.ProductId,
        p.SKU,
        p.ProductName
),

Ranked AS
(
    SELECT
        *,

        ROW_NUMBER() OVER
        (
            PARTITION BY CategoryName
            ORDER BY Revenue DESC
        ) AS CategoryProductRank

    FROM ProductRevenue
)

SELECT
    CategoryName,
    CategoryProductRank,

    SKU,
    ProductName,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS Revenue

FROM Ranked

WHERE
    CategoryProductRank <= 5

ORDER BY
    CategoryName,
    CategoryProductRank;
GO


/* =========================================================
   4. BRAND PERFORMANCE
   ========================================================= */

SELECT
    b.BrandName,

    COUNT(
        DISTINCT p.ProductId
    ) AS Products,

    SUM(
        i.Quantity
    ) AS UnitsSold,

    CAST(
        SUM(
            i.NetAmount
        )
        AS DECIMAL(19,2)
    ) AS PreReturnNetSales,

    CAST(
        SUM(
            i.NetAmount
            - i.LineCOGS
        )
        AS DECIMAL(19,2)
    ) AS PreReturnGrossProfit,

    RANK() OVER
    (
        ORDER BY
            SUM(
                i.NetAmount
            ) DESC
    ) AS BrandRevenueRank

FROM sales.SalesOrderItem i

INNER JOIN sales.SalesOrder o
    ON i.OrderId = o.OrderId

INNER JOIN product.Product p
    ON i.ProductId = p.ProductId

INNER JOIN product.Brand b
    ON p.BrandId = b.BrandId

WHERE
    o.OrderStatus = 'COMPLETED'

GROUP BY
    b.BrandName

ORDER BY
    BrandRevenueRank;
GO


/* =========================================================
   5. PRODUCTS WITH HIGH RETURN RATE

   Minimum 100 gross units prevents tiny-volume products
   from dominating anomaly analysis.
   ========================================================= */

WITH Sales AS
(
    SELECT
        ProductId,

        SUM(
            Quantity
        ) AS GrossUnits

    FROM sales.SalesOrderItem

    GROUP BY
        ProductId
),

Returns AS
(
    SELECT
        i.ProductId,

        SUM(
            r.ReturnQuantity
        ) AS ReturnedUnits

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    GROUP BY
        i.ProductId
)

SELECT TOP (20)

    p.SKU,
    p.ProductName,

    c.CategoryName,

    s.GrossUnits,

    COALESCE(
        r.ReturnedUnits,
        0
    ) AS ReturnedUnits,

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

FROM Sales s

INNER JOIN product.Product p
    ON s.ProductId = p.ProductId

INNER JOIN product.Subcategory sc
    ON p.SubcategoryId
       = sc.SubcategoryId

INNER JOIN product.Category c
    ON sc.CategoryId
       = c.CategoryId

LEFT JOIN Returns r
    ON s.ProductId
       = r.ProductId

WHERE
    s.GrossUnits >= 100

ORDER BY
    ReturnRatePct DESC,
    s.GrossUnits DESC;
GO