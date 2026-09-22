/*
============================================================
 UAE Retail Intelligence Platform
 File: 06_returns_analysis.sql

 Returns Analytics

 Includes:
 - Overall return KPIs
 - Return reasons
 - Category return rates
 - Store return rates
 - Monthly return trend
 - Product anomaly analysis
 - Product vs category baseline
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. OVERALL RETURN KPIs
   ========================================================= */

WITH Sales AS
(
    SELECT
        SUM(Quantity)
            AS GrossUnits,

        SUM(NetAmount)
            AS NetSalesBeforeReturns

    FROM sales.SalesOrderItem
),

Returns AS
(
    SELECT
        SUM(ReturnQuantity)
            AS ReturnedUnits,

        SUM(ReturnedNetAmount)
            AS ReturnedNetSales,

        SUM(RefundAmount)
            AS RefundAmount

    FROM sales.ReturnItem
)

SELECT
    s.GrossUnits,

    r.ReturnedUnits,

    CAST(
        r.ReturnedUnits
        * 100.0
        / NULLIF(
            s.GrossUnits,
            0
        )
        AS DECIMAL(10,2)
    ) AS UnitReturnRatePct,

    CAST(
        r.ReturnedNetSales
        * 100.0
        / NULLIF(
            s.NetSalesBeforeReturns,
            0
        )
        AS DECIMAL(10,2)
    ) AS ValueReturnRatePct,

    CAST(
        r.ReturnedNetSales
        AS DECIMAL(19,2)
    ) AS ReturnedNetSales,

    CAST(
        r.RefundAmount
        AS DECIMAL(19,2)
    ) AS RefundAmount

FROM Sales s
CROSS JOIN Returns r;
GO


/* =========================================================
   2. RETURN REASONS
   ========================================================= */

SELECT
    ReturnReason,

    COUNT_BIG(*)
        AS ReturnLines,

    SUM(
        ReturnQuantity
    ) AS ReturnedUnits,

    CAST(
        SUM(
            ReturnedNetAmount
        )
        AS DECIMAL(19,2)
    ) AS ReturnedNetSales,

    CAST(
        SUM(
            ReturnedNetAmount
        )
        * 100.0
        /
        SUM(
            SUM(
                ReturnedNetAmount
            )
        ) OVER ()
        AS DECIMAL(10,2)
    ) AS ReturnedValueContributionPct

FROM sales.ReturnItem

GROUP BY
    ReturnReason

ORDER BY
    ReturnedNetSales DESC;
GO


/* =========================================================
   3. RETURN RATE BY CATEGORY
   ========================================================= */

WITH Sold AS
(
    SELECT
        c.CategoryId,
        c.CategoryName,

        SUM(
            i.Quantity
        ) AS GrossUnits

    FROM sales.SalesOrderItem i

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory s
        ON p.SubcategoryId
           = s.SubcategoryId

    INNER JOIN product.Category c
        ON s.CategoryId
           = c.CategoryId

    GROUP BY
        c.CategoryId,
        c.CategoryName
),

Returned AS
(
    SELECT
        c.CategoryId,

        SUM(
            r.ReturnQuantity
        ) AS ReturnedUnits

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    INNER JOIN product.Product p
        ON i.ProductId
           = p.ProductId

    INNER JOIN product.Subcategory s
        ON p.SubcategoryId
           = s.SubcategoryId

    INNER JOIN product.Category c
        ON s.CategoryId
           = c.CategoryId

    GROUP BY
        c.CategoryId
)

SELECT
    s.CategoryName,

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
    ) AS ReturnRatePct,

    RANK() OVER
    (
        ORDER BY
            COALESCE(
                r.ReturnedUnits,
                0
            )
            * 1.0
            / NULLIF(
                s.GrossUnits,
                0
            )
            DESC
    ) AS ReturnRateRank

FROM Sold s

LEFT JOIN Returned r
    ON s.CategoryId
       = r.CategoryId

ORDER BY
    ReturnRateRank;
GO


/* =========================================================
   4. STORE RETURN RATE
   ========================================================= */

WITH Sold AS
(
    SELECT
        o.StoreId,

        SUM(
            i.Quantity
        ) AS GrossUnits

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    GROUP BY
        o.StoreId
),

Returned AS
(
    SELECT
        o.StoreId,

        SUM(
            r.ReturnQuantity
        ) AS ReturnedUnits

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    GROUP BY
        o.StoreId
)

SELECT
    st.StoreCode,
    st.StoreName,

    e.EmirateName,

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
    ) AS ReturnRatePct,

    RANK() OVER
    (
        ORDER BY
            COALESCE(
                r.ReturnedUnits,
                0
            )
            * 1.0
            / NULLIF(
                s.GrossUnits,
                0
            )
            DESC
    ) AS ReturnRateRank

FROM Sold s

INNER JOIN core.Store st
    ON s.StoreId
       = st.StoreId

INNER JOIN core.City c
    ON st.CityId
       = c.CityId

INNER JOIN core.Emirate e
    ON c.EmirateId
       = e.EmirateId

LEFT JOIN Returned r
    ON s.StoreId
       = r.StoreId

ORDER BY
    ReturnRateRank;
GO


/* =========================================================
   5. MONTHLY RETURN TREND

   Return is attributed to original sales month so denominator
   and numerator refer to the same sold population.
   ========================================================= */

WITH Sold AS
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
            i.Quantity
        ) AS GrossUnits

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

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

Returned AS
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
            r.ReturnQuantity
        ) AS ReturnedUnits

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

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

FROM Sold s

LEFT JOIN Returned r
    ON s.MonthStart
       = r.MonthStart

ORDER BY
    s.MonthStart;
GO


/* =========================================================
   6. PRODUCT RETURN ANOMALY

   Compare each product's return rate against the return rate
   of its own category.

   Minimum 50 units sold removes very low-volume noise.
   ========================================================= */

WITH ProductSold AS
(
    SELECT
        p.ProductId,

        c.CategoryId,
        c.CategoryName,

        SUM(
            i.Quantity
        ) AS GrossUnits

    FROM sales.SalesOrderItem i

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory s
        ON p.SubcategoryId
           = s.SubcategoryId

    INNER JOIN product.Category c
        ON s.CategoryId
           = c.CategoryId

    GROUP BY
        p.ProductId,
        c.CategoryId,
        c.CategoryName
),

ProductReturned AS
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
),

ProductMetrics AS
(
    SELECT
        s.ProductId,
        s.CategoryId,
        s.CategoryName,

        s.GrossUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        )
        * 1.0
        / NULLIF(
            s.GrossUnits,
            0
        ) AS ProductReturnRate

    FROM ProductSold s

    LEFT JOIN ProductReturned r
        ON s.ProductId
           = r.ProductId
),

CategoryMetrics AS
(
    SELECT
        CategoryId,

        SUM(
            ReturnedUnits
        )
        * 1.0
        /
        NULLIF(
            SUM(
                GrossUnits
            ),
            0
        ) AS CategoryReturnRate

    FROM ProductMetrics

    GROUP BY
        CategoryId
)

SELECT TOP (30)

    p.SKU,
    p.ProductName,

    m.CategoryName,

    m.GrossUnits,
    m.ReturnedUnits,

    CAST(
        m.ProductReturnRate
        * 100
        AS DECIMAL(10,2)
    ) AS ProductReturnRatePct,

    CAST(
        c.CategoryReturnRate
        * 100
        AS DECIMAL(10,2)
    ) AS CategoryReturnRatePct,

    CAST(
        (
            m.ProductReturnRate
            - c.CategoryReturnRate
        )
        * 100
        AS DECIMAL(10,2)
    ) AS ExcessReturnRatePctPoints,

    CAST(
        m.ProductReturnRate
        /
        NULLIF(
            c.CategoryReturnRate,
            0
        )
        AS DECIMAL(10,2)
    ) AS CategoryRateMultiplier

FROM ProductMetrics m

INNER JOIN CategoryMetrics c
    ON m.CategoryId
       = c.CategoryId

INNER JOIN product.Product p
    ON m.ProductId
       = p.ProductId

WHERE
    m.GrossUnits >= 50

ORDER BY
    CategoryRateMultiplier DESC,
    m.GrossUnits DESC;
GO


/* =========================================================
   7. QUARTERLY PRODUCT RETURN ANOMALY

   This is more sensitive to temporary quality problems than
   the lifetime product return rate.
   ========================================================= */

WITH ProductQuarterSales AS
(
    SELECT
        p.ProductId,

        c.CategoryId,
        c.CategoryName,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        DATEPART(
            QUARTER,
            o.OrderDateTime
        ) AS SalesQuarter,

        SUM(
            i.Quantity
        ) AS GrossUnits

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    INNER JOIN product.Product p
        ON i.ProductId = p.ProductId

    INNER JOIN product.Subcategory s
        ON p.SubcategoryId
           = s.SubcategoryId

    INNER JOIN product.Category c
        ON s.CategoryId
           = c.CategoryId

    GROUP BY
        p.ProductId,
        c.CategoryId,
        c.CategoryName,

        YEAR(
            o.OrderDateTime
        ),

        DATEPART(
            QUARTER,
            o.OrderDateTime
        )
),

ProductQuarterReturns AS
(
    SELECT
        i.ProductId,

        YEAR(
            o.OrderDateTime
        ) AS SalesYear,

        DATEPART(
            QUARTER,
            o.OrderDateTime
        ) AS SalesQuarter,

        SUM(
            r.ReturnQuantity
        ) AS ReturnedUnits

    FROM sales.ReturnItem r

    INNER JOIN sales.SalesOrderItem i
        ON r.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    GROUP BY
        i.ProductId,

        YEAR(
            o.OrderDateTime
        ),

        DATEPART(
            QUARTER,
            o.OrderDateTime
        )
),

Metrics AS
(
    SELECT
        s.*,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        )
        * 1.0
        / NULLIF(
            s.GrossUnits,
            0
        ) AS ReturnRate

    FROM ProductQuarterSales s

    LEFT JOIN ProductQuarterReturns r
        ON s.ProductId
           = r.ProductId

        AND s.SalesYear
           = r.SalesYear

        AND s.SalesQuarter
           = r.SalesQuarter
),

CategoryQuarter AS
(
    SELECT
        CategoryId,
        SalesYear,
        SalesQuarter,

        SUM(
            ReturnedUnits
        )
        * 1.0
        /
        NULLIF(
            SUM(
                GrossUnits
            ),
            0
        ) AS CategoryReturnRate

    FROM Metrics

    GROUP BY
        CategoryId,
        SalesYear,
        SalesQuarter
)

SELECT TOP (50)

    m.SalesYear,
    m.SalesQuarter,

    p.SKU,
    p.ProductName,

    m.CategoryName,

    m.GrossUnits,
    m.ReturnedUnits,

    CAST(
        m.ReturnRate
        * 100
        AS DECIMAL(10,2)
    ) AS ProductReturnRatePct,

    CAST(
        c.CategoryReturnRate
        * 100
        AS DECIMAL(10,2)
    ) AS CategoryReturnRatePct,

    CAST(
        m.ReturnRate
        /
        NULLIF(
            c.CategoryReturnRate,
            0
        )
        AS DECIMAL(10,2)
    ) AS CategoryRateMultiplier

FROM Metrics m

INNER JOIN CategoryQuarter c
    ON m.CategoryId
       = c.CategoryId

    AND m.SalesYear
       = c.SalesYear

    AND m.SalesQuarter
       = c.SalesQuarter

INNER JOIN product.Product p
    ON m.ProductId
       = p.ProductId

WHERE
    m.GrossUnits >= 20

ORDER BY
    CategoryRateMultiplier DESC,
    m.ReturnedUnits DESC;
GO