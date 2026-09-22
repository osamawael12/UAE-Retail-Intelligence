/*
============================================================
 UAE Retail Intelligence Platform
 File: 01_sales_views.sql

 Analytics Sales Layer

 Views:
 - analytics.vw_SalesDetail
 - analytics.vw_DailySales

 Revenue definition:
 Net Sales - Returned Net Sales

 Gross Profit:
 Revenue - Net COGS

 VAT is excluded from Revenue.
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. SALES DETAIL VIEW

   Grain:
   One row per SalesOrderItem.

   Returns are pre-aggregated by OrderItemId so multiple
   ReturnItems cannot duplicate sales rows.
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_SalesDetail
AS

WITH ReturnAggregation AS
(
    SELECT
        ri.OrderItemId,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedQuantity,

        SUM(
            ri.ReturnedNetAmount
        ) AS ReturnedNetSales,

        SUM(
            ri.VATReversed
        ) AS VATReversed,

        SUM(
            ri.RefundAmount
        ) AS RefundAmount

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId
           = r.ReturnId

    WHERE
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        ri.OrderItemId
)

SELECT
    /* Order */

    o.OrderId,
    o.OrderNumber,
    o.OrderDateTime,
    o.DateKey,
    o.OrderStatus,

    /* Calendar */

    d.FullDate,
    d.DayName,
    d.DayOfWeekNumber,
    d.WeekOfYear,
    d.MonthNumber,
    d.MonthName,
    d.QuarterNumber,
    d.YearNumber,

    d.IsWeekend,
    d.IsRamadan,
    d.IsEidAlFitr,
    d.IsEidAlAdha,
    d.IsWhiteFriday,
    d.IsEidAlEtihad,
    d.IsSummer,
    d.IsYearEndSeason,

    /* Geography */

    e.EmirateId,
    e.EmirateCode,
    e.EmirateName,

    city.CityId,
    city.CityName,

    s.StoreId,
    s.StoreCode,
    s.StoreName,
    s.StoreType,

    /* Channel */

    ch.SalesChannelId,
    ch.ChannelCode,
    ch.ChannelName,

    /* Customer */

    c.CustomerId,
    c.CustomerCode,
    c.Nationality,
    c.RegistrationDate,

    /* Product */

    i.OrderItemId,

    p.ProductId,
    p.SKU,
    p.ProductName,

    cat.CategoryId,
    cat.CategoryName,

    sc.SubcategoryId,
    sc.SubcategoryName,

    b.BrandId,
    b.BrandName,

    /* Promotion */

    i.PromotionId,
    pr.PromotionCode,
    pr.PromotionName,
    pr.PromotionType,

    /* Sales */

    i.Quantity
        AS GrossUnits,

    i.UnitPrice,
    i.UnitCost,

    i.GrossAmount
        AS GrossSales,

    i.DiscountAmount,

    i.NetAmount
        AS NetSalesBeforeReturns,

    i.VATRate,
    i.VATAmount,

    i.CustomerTotal,

    i.LineCOGS
        AS SalesCOGS,

    /* Returns */

    COALESCE(
        r.ReturnedQuantity,
        0
    ) AS ReturnedUnits,

    COALESCE(
        r.ReturnedNetSales,
        0
    ) AS ReturnedNetSales,

    COALESCE(
        r.VATReversed,
        0
    ) AS VATReversed,

    COALESCE(
        r.RefundAmount,
        0
    ) AS RefundAmount,

    /* Net Units */

    i.Quantity
        - COALESCE(
            r.ReturnedQuantity,
            0
        )
        AS NetUnits,

    /* Revenue */

    i.NetAmount
        - COALESCE(
            r.ReturnedNetSales,
            0
        )
        AS Revenue,

    /* Returned COGS */

    i.UnitCost
        * COALESCE(
            r.ReturnedQuantity,
            0
        )
        AS ReturnedCOGS,

    /* Net COGS */

    i.LineCOGS
        -
        (
            i.UnitCost
            * COALESCE(
                r.ReturnedQuantity,
                0
            )
        )
        AS NetCOGS,

    /* Gross Profit */

    (
        i.NetAmount
        - COALESCE(
            r.ReturnedNetSales,
            0
        )
    )
    -
    (
        i.LineCOGS
        -
        (
            i.UnitCost
            * COALESCE(
                r.ReturnedQuantity,
                0
            )
        )
    )
        AS GrossProfit

FROM sales.SalesOrderItem i

INNER JOIN sales.SalesOrder o
    ON i.OrderId
       = o.OrderId

INNER JOIN core.DateDimension d
    ON o.DateKey
       = d.DateKey

INNER JOIN core.Store s
    ON o.StoreId
       = s.StoreId

INNER JOIN core.City city
    ON s.CityId
       = city.CityId

INNER JOIN core.Emirate e
    ON city.EmirateId
       = e.EmirateId

INNER JOIN core.SalesChannel ch
    ON o.SalesChannelId
       = ch.SalesChannelId

INNER JOIN customer.Customer c
    ON o.CustomerId
       = c.CustomerId

INNER JOIN product.Product p
    ON i.ProductId
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

LEFT JOIN sales.Promotion pr
    ON i.PromotionId
       = pr.PromotionId

LEFT JOIN ReturnAggregation r
    ON i.OrderItemId
       = r.OrderItemId

WHERE
    o.OrderStatus
    = 'COMPLETED';
GO


/* =========================================================
   2. DAILY SALES VIEW

   Grain:
   Date x Store x Channel

   Useful for:
   - Dashboards
   - Time Series EDA
   - Forecasting
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_DailySales
AS

SELECT
    FullDate,
    DateKey,

    YearNumber,
    MonthNumber,
    QuarterNumber,
    DayName,

    IsWeekend,
    IsRamadan,
    IsEidAlFitr,
    IsEidAlAdha,
    IsWhiteFriday,
    IsEidAlEtihad,
    IsSummer,
    IsYearEndSeason,

    EmirateId,
    EmirateName,

    StoreId,
    StoreCode,
    StoreName,

    SalesChannelId,
    ChannelCode,
    ChannelName,

    COUNT(
        DISTINCT OrderId
    ) AS Orders,

    COUNT(
        DISTINCT CustomerId
    ) AS Customers,

    SUM(
        GrossUnits
    ) AS GrossUnits,

    SUM(
        ReturnedUnits
    ) AS ReturnedUnits,

    SUM(
        NetUnits
    ) AS NetUnits,

    SUM(
        GrossSales
    ) AS GrossSales,

    SUM(
        DiscountAmount
    ) AS DiscountAmount,

    SUM(
        NetSalesBeforeReturns
    ) AS NetSalesBeforeReturns,

    SUM(
        ReturnedNetSales
    ) AS ReturnedNetSales,

    SUM(
        Revenue
    ) AS Revenue,

    SUM(
        SalesCOGS
    ) AS SalesCOGS,

    SUM(
        ReturnedCOGS
    ) AS ReturnedCOGS,

    SUM(
        NetCOGS
    ) AS NetCOGS,

    SUM(
        GrossProfit
    ) AS GrossProfit,

    SUM(
        VATAmount
    ) AS VATCollected,

    SUM(
        VATReversed
    ) AS VATReversed,

    SUM(
        RefundAmount
    ) AS RefundAmount

FROM analytics.vw_SalesDetail

GROUP BY
    FullDate,
    DateKey,

    YearNumber,
    MonthNumber,
    QuarterNumber,
    DayName,

    IsWeekend,
    IsRamadan,
    IsEidAlFitr,
    IsEidAlAdha,
    IsWhiteFriday,
    IsEidAlEtihad,
    IsSummer,
    IsYearEndSeason,

    EmirateId,
    EmirateName,

    StoreId,
    StoreCode,
    StoreName,

    SalesChannelId,
    ChannelCode,
    ChannelName;
GO



