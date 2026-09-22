/*
============================================================
 UAE Retail Intelligence Platform
 File: 02_business_performance_views.sql

 Views:
 - analytics.vw_StorePerformance
 - analytics.vw_ProductPerformance
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   STORE PERFORMANCE

   Grain:
   One row per Store.
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_StorePerformance
AS

SELECT
    StoreId,
    StoreCode,
    StoreName,

    EmirateId,
    EmirateName,

    COUNT(
        DISTINCT OrderId
    ) AS Orders,

    COUNT(
        DISTINCT CustomerId
    ) AS Customers,

    SUM(
        NetUnits
    ) AS NetUnits,

    SUM(
        Revenue
    ) AS Revenue,

    SUM(
        GrossProfit
    ) AS GrossProfit,

    CASE
        WHEN
            SUM(Revenue) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    GrossProfit
                )
                * 100.0
                / SUM(
                    Revenue
                )
                AS DECIMAL(19,6)
            )
    END AS GrossMarginPct,

    CASE
        WHEN
            COUNT(
                DISTINCT OrderId
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    Revenue
                )
                /
                COUNT(
                    DISTINCT OrderId
                )
                AS DECIMAL(19,6)
            )
    END AS AOV,

    SUM(
        GrossUnits
    ) AS GrossUnits,

    SUM(
        ReturnedUnits
    ) AS ReturnedUnits,

    CASE
        WHEN
            SUM(
                GrossUnits
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    ReturnedUnits
                )
                * 100.0
                /
                SUM(
                    GrossUnits
                )
                AS DECIMAL(19,6)
            )
    END AS ReturnRatePct

FROM analytics.vw_SalesDetail

GROUP BY
    StoreId,
    StoreCode,
    StoreName,
    EmirateId,
    EmirateName;
GO


/* =========================================================
   PRODUCT PERFORMANCE

   Grain:
   One row per Product.
   ========================================================= */

CREATE OR ALTER VIEW analytics.vw_ProductPerformance
AS

SELECT
    ProductId,
    SKU,
    ProductName,

    CategoryId,
    CategoryName,

    SubcategoryId,
    SubcategoryName,

    BrandId,
    BrandName,

    COUNT(
        DISTINCT OrderId
    ) AS Orders,

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
        Revenue
    ) AS Revenue,

    SUM(
        NetCOGS
    ) AS NetCOGS,

    SUM(
        GrossProfit
    ) AS GrossProfit,

    CASE
        WHEN
            SUM(
                Revenue
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    GrossProfit
                )
                * 100.0
                /
                SUM(
                    Revenue
                )
                AS DECIMAL(19,6)
            )
    END AS GrossMarginPct,

    CASE
        WHEN
            SUM(
                GrossUnits
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    ReturnedUnits
                )
                * 100.0
                /
                SUM(
                    GrossUnits
                )
                AS DECIMAL(19,6)
            )
    END AS ReturnRatePct,

    CASE
        WHEN
            SUM(
                NetSalesBeforeReturns
            ) = 0
            THEN CAST(
                0
                AS DECIMAL(19,6)
            )

        ELSE
            CAST(
                SUM(
                    CASE
                        WHEN
                            DiscountAmount
                            > 0

                            THEN
                            NetSalesBeforeReturns

                        ELSE 0
                    END
                )
                * 100.0
                /
                SUM(
                    NetSalesBeforeReturns
                )
                AS DECIMAL(19,6)
            )
    END AS DiscountDependencyPct

FROM analytics.vw_SalesDetail

GROUP BY
    ProductId,
    SKU,
    ProductName,

    CategoryId,
    CategoryName,

    SubcategoryId,
    SubcategoryName,

    BrandId,
    BrandName;
GO