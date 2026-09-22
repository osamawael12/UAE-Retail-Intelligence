/*
============================================================
 UAE Retail Intelligence Platform
 File: 03_customer_returns_views.sql

 Views:
 - analytics.vw_Customer360
 - analytics.vw_ReturnAnalysis
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   CUSTOMER 360

   Grain:
   One row per registered customer.

   Customers who never purchased are retained.

   Reference date:
   2025-12-31
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_Customer360
AS

WITH CustomerSales AS
(
    SELECT
        o.CustomerId,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        SUM(
            i.Quantity
        ) AS GrossUnits,

        SUM(
            i.NetAmount
        ) AS NetSalesBeforeReturns,

        SUM(
            i.LineCOGS
        ) AS SalesCOGS,

        MIN(
            o.OrderDateTime
        ) AS FirstPurchaseDate,

        MAX(
            o.OrderDateTime
        ) AS LastPurchaseDate

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

    WHERE
        o.OrderStatus
        = 'COMPLETED'

    GROUP BY
        o.CustomerId
),

CustomerReturns AS
(
    SELECT
        o.CustomerId,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            i.UnitCost
            * ri.ReturnQuantity
        ) AS ReturnedCOGS,

        SUM(
            ri.RefundAmount
        ) AS RefundAmount

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
        o.CustomerId
)

SELECT
    c.CustomerId,
    c.CustomerCode,

    c.FirstName,
    c.LastName,

    c.Gender,
    c.DateOfBirth,
    c.Nationality,

    c.RegistrationDate,

    c.PreferredEmirateId,
    e.EmirateName
        AS PreferredEmirateName,

    c.PreferredChannelId,
    ch.ChannelName
        AS PreferredChannelName,

    c.IsActive,

    COALESCE(
        s.Orders,
        0
    ) AS Orders,

    COALESCE(
        s.GrossUnits,
        0
    ) AS GrossUnits,

    COALESCE(
        r.ReturnedUnits,
        0
    ) AS ReturnedUnits,

    COALESCE(
        s.GrossUnits,
        0
    )
    -
    COALESCE(
        r.ReturnedUnits,
        0
    ) AS NetUnits,

    COALESCE(
        s.NetSalesBeforeReturns,
        0
    )
    -
    COALESCE(
        r.ReturnedNetSales,
        0
    ) AS Revenue,

    COALESCE(
        s.SalesCOGS,
        0
    )
    -
    COALESCE(
        r.ReturnedCOGS,
        0
    ) AS NetCOGS,

    (
        COALESCE(
            s.NetSalesBeforeReturns,
            0
        )
        -
        COALESCE(
            r.ReturnedNetSales,
            0
        )
    )
    -
    (
        COALESCE(
            s.SalesCOGS,
            0
        )
        -
        COALESCE(
            r.ReturnedCOGS,
            0
        )
    ) AS GrossProfit,

    COALESCE(
        r.RefundAmount,
        0
    ) AS RefundAmount,

    s.FirstPurchaseDate,
    s.LastPurchaseDate,

    CASE
        WHEN
            s.LastPurchaseDate
            IS NULL
            THEN NULL

        ELSE
            DATEDIFF(
                DAY,
                CAST(
                    s.LastPurchaseDate
                    AS DATE
                ),
                '2025-12-31'
            )
    END AS RecencyDays,

    CASE
        WHEN
            COALESCE(
                s.Orders,
                0
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                (
                    COALESCE(
                        s.NetSalesBeforeReturns,
                        0
                    )
                    -
                    COALESCE(
                        r.ReturnedNetSales,
                        0
                    )
                )
                /
                s.Orders
                AS DECIMAL(19,6)
            )
    END AS AOV,

    CASE
        WHEN
            COALESCE(
                s.GrossUnits,
                0
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                COALESCE(
                    r.ReturnedUnits,
                    0
                )
                * 100.0
                /
                s.GrossUnits
                AS DECIMAL(19,6)
            )
    END AS ReturnRatePct,

    CASE
        WHEN
            COALESCE(
                s.Orders,
                0
            ) >= 2
            THEN CAST(
                1
                AS BIT
            )

        ELSE
            CAST(
                0
                AS BIT
            )
    END AS IsRepeatCustomer

FROM customer.Customer c

LEFT JOIN CustomerSales s
    ON c.CustomerId
       = s.CustomerId

LEFT JOIN CustomerReturns r
    ON c.CustomerId
       = r.CustomerId

LEFT JOIN core.Emirate e
    ON c.PreferredEmirateId
       = e.EmirateId

LEFT JOIN core.SalesChannel ch
    ON c.PreferredChannelId
       = ch.SalesChannelId;
GO


/* =========================================================
   RETURN ANALYSIS

   Grain:
   One row per ReturnItem.

   Contains original sale context and return context.
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_ReturnAnalysis
AS

SELECT
    r.ReturnId,
    r.ReturnNumber,

    ri.ReturnItemId,

    r.ReturnDateTime,
    r.DateKey
        AS ReturnDateKey,

    CAST(
        r.ReturnDateTime
        AS DATE
    ) AS ReturnDate,

    r.ReturnStatus,

    /* Original sale */

    o.OrderId,
    o.OrderNumber,
    o.OrderDateTime,

    CAST(
        o.OrderDateTime
        AS DATE
    ) AS OrderDate,

    DATEDIFF(
        DAY,
        CAST(
            o.OrderDateTime
            AS DATE
        ),
        CAST(
            r.ReturnDateTime
            AS DATE
        )
    ) AS ReturnLagDays,

    /* Geography */

    e.EmirateId,
    e.EmirateName,

    s.StoreId,
    s.StoreCode,
    s.StoreName,

    /* Customer */

    o.CustomerId,
    c.CustomerCode,

    /* Product */

    oi.ProductId,
    p.SKU,
    p.ProductName,

    cat.CategoryId,
    cat.CategoryName,

    sc.SubcategoryId,
    sc.SubcategoryName,

    b.BrandId,
    b.BrandName,

    /* Original sales line */

    oi.Quantity
        AS SoldQuantity,

    oi.UnitPrice,
    oi.UnitCost,

    oi.NetAmount
        AS OriginalLineNetSales,

    /* Return */

    ri.ReturnQuantity,
    ri.ReturnReason,

    ri.ReturnedNetAmount,
    ri.VATReversed,
    ri.RefundAmount,

    ri.IsRestockable,

    oi.UnitCost
        * ri.ReturnQuantity
        AS ReturnedCOGS,

    CASE
        WHEN
            oi.Quantity = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                ri.ReturnQuantity
                * 100.0
                / oi.Quantity
                AS DECIMAL(19,6)
            )
    END AS LineQuantityReturnPct

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

INNER JOIN core.Store s
    ON o.StoreId
       = s.StoreId

INNER JOIN core.City city
    ON s.CityId
       = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

INNER JOIN customer.Customer c
    ON o.CustomerId
       = c.CustomerId

INNER JOIN product.Product p
    ON oi.ProductId
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

WHERE
    r.ReturnStatus
    = 'COMPLETED';
GO