/*
============================================================
 UAE Retail Intelligence Platform
 File: 05_customer_analysis.sql

 Customer Analytics

 Includes:
 - Customer base summary
 - Active purchasing customers
 - New vs returning customers
 - Repeat customer rate
 - Purchase frequency
 - Customer lifetime metrics
 - Customer ranking
 - Top customers
 - Customer value distribution

 Revenue excludes VAT and valid returned merchandise.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. CUSTOMER BASE SUMMARY
   ========================================================= */

WITH CustomerOrders AS
(
    SELECT
        o.CustomerId,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        MIN(
            o.OrderDateTime
        ) AS FirstPurchaseDate,

        MAX(
            o.OrderDateTime
        ) AS LastPurchaseDate,

        SUM(
            i.NetAmount
        ) AS NetSalesBeforeReturns

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

    WHERE
        o.OrderStatus = 'COMPLETED'

    GROUP BY
        o.CustomerId
),

CustomerReturns AS
(
    SELECT
        o.CustomerId,

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
        r.ReturnStatus
        = 'COMPLETED'

    GROUP BY
        o.CustomerId
),

Metrics AS
(
    SELECT
        c.CustomerId,

        COALESCE(
            o.Orders,
            0
        ) AS Orders,

        o.FirstPurchaseDate,
        o.LastPurchaseDate,

        COALESCE(
            o.NetSalesBeforeReturns,
            0
        )
        -
        COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Revenue

    FROM customer.Customer c

    LEFT JOIN CustomerOrders o
        ON c.CustomerId
           = o.CustomerId

    LEFT JOIN CustomerReturns r
        ON c.CustomerId
           = r.CustomerId
)

SELECT
    COUNT_BIG(*)
        AS RegisteredCustomers,

    SUM(
        CASE
            WHEN Orders > 0
                THEN 1
            ELSE 0
        END
    ) AS PurchasingCustomers,

    SUM(
        CASE
            WHEN Orders >= 2
                THEN 1
            ELSE 0
        END
    ) AS RepeatCustomers,

    CAST(
        SUM(
            CASE
                WHEN Orders >= 2
                    THEN 1.0
                ELSE 0.0
            END
        )
        * 100.0
        /
        NULLIF(
            SUM(
                CASE
                    WHEN Orders > 0
                        THEN 1.0
                    ELSE 0.0
                END
            ),
            0
        )
        AS DECIMAL(10,2)
    ) AS RepeatCustomerRatePct,

    CAST(
        SUM(
            Orders
        )
        * 1.0
        /
        NULLIF(
            SUM(
                CASE
                    WHEN Orders > 0
                        THEN 1
                    ELSE 0
                END
            ),
            0
        )
        AS DECIMAL(10,2)
    ) AS PurchaseFrequency,

    CAST(
        SUM(
            Revenue
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN Orders > 0
                        THEN 1
                    ELSE 0
                END
            ),
            0
        )
        AS DECIMAL(19,2)
    ) AS RevenuePerPurchasingCustomer

FROM Metrics;
GO


/* =========================================================
   2. CUSTOMER LIFETIME METRICS
   ========================================================= */

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
        ) AS NetSales,

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
            ri.ReturnedNetAmount
        ) AS Returns,

        SUM(
            ri.ReturnQuantity
        ) AS ReturnedUnits

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
),

Metrics AS
(
    SELECT
        c.CustomerId,
        c.CustomerCode,

        c.FirstName,
        c.LastName,

        c.Nationality,

        s.Orders,

        s.FirstPurchaseDate,
        s.LastPurchaseDate,

        s.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue,

        s.GrossUnits
        - COALESCE(
            r.ReturnedUnits,
            0
        ) AS NetUnits,

        COALESCE(
            r.ReturnedUnits,
            0
        ) AS ReturnedUnits,

        s.GrossUnits

    FROM CustomerSales s

    INNER JOIN customer.Customer c
        ON s.CustomerId
           = c.CustomerId

    LEFT JOIN CustomerReturns r
        ON s.CustomerId
           = r.CustomerId
)

SELECT
    CustomerId,
    CustomerCode,

    FirstName,
    LastName,

    Nationality,

    Orders,

    NetUnits,

    CAST(
        Revenue
        AS DECIMAL(19,2)
    ) AS LifetimeRevenue,

    CAST(
        Revenue
        / NULLIF(
            Orders,
            0
        )
        AS DECIMAL(19,2)
    ) AS CustomerAOV,

    FirstPurchaseDate,
    LastPurchaseDate,

    DATEDIFF(
        DAY,
        CAST(
            LastPurchaseDate
            AS DATE
        ),
        '2025-12-31'
    ) AS DaysSinceLastPurchase,

    DATEDIFF(
        DAY,
        CAST(
            FirstPurchaseDate
            AS DATE
        ),
        CAST(
            LastPurchaseDate
            AS DATE
        )
    ) AS CustomerPurchaseSpanDays,

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
    ) AS RevenueRank,

    RANK() OVER
    (
        ORDER BY Orders DESC
    ) AS FrequencyRank

FROM Metrics

ORDER BY
    RevenueRank;
GO


/* =========================================================
   3. NEW VS RETURNING CUSTOMERS BY MONTH

   New:
   First-ever completed purchase is in that month.

   Returning:
   Customer purchased during the month and had a first
   purchase before that month.
   ========================================================= */

WITH CustomerFirstPurchase AS
(
    SELECT
        CustomerId,

        MIN(
            CAST(
                OrderDateTime
                AS DATE
            )
        ) AS FirstPurchaseDate

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
),

MonthlyCustomers AS
(
    SELECT DISTINCT
        o.CustomerId,

        DATEFROMPARTS(
            YEAR(
                o.OrderDateTime
            ),
            MONTH(
                o.OrderDateTime
            ),
            1
        ) AS MonthStart

    FROM sales.SalesOrder o

    WHERE
        o.OrderStatus
        = 'COMPLETED'
)

SELECT
    m.MonthStart,

    COUNT_BIG(*)
        AS ActiveCustomers,

    SUM(
        CASE
            WHEN
                DATEFROMPARTS(
                    YEAR(
                        f.FirstPurchaseDate
                    ),
                    MONTH(
                        f.FirstPurchaseDate
                    ),
                    1
                )
                = m.MonthStart

                THEN 1
            ELSE 0
        END
    ) AS NewCustomers,

    SUM(
        CASE
            WHEN
                DATEFROMPARTS(
                    YEAR(
                        f.FirstPurchaseDate
                    ),
                    MONTH(
                        f.FirstPurchaseDate
                    ),
                    1
                )
                < m.MonthStart

                THEN 1
            ELSE 0
        END
    ) AS ReturningCustomers,

    CAST(
        SUM(
            CASE
                WHEN
                    DATEFROMPARTS(
                        YEAR(
                            f.FirstPurchaseDate
                        ),
                        MONTH(
                            f.FirstPurchaseDate
                        ),
                        1
                    )
                    < m.MonthStart

                    THEN 1.0
                ELSE 0.0
            END
        )
        * 100.0
        /
        NULLIF(
            COUNT_BIG(*),
            0
        )
        AS DECIMAL(10,2)
    ) AS ReturningCustomerPct

FROM MonthlyCustomers m

INNER JOIN CustomerFirstPurchase f
    ON m.CustomerId
       = f.CustomerId

GROUP BY
    m.MonthStart

ORDER BY
    m.MonthStart;
GO


/* =========================================================
   4. TOP 20 CUSTOMERS BY REVENUE
   ========================================================= */

WITH Sales AS
(
    SELECT
        o.CustomerId,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Orders,

        SUM(
            i.NetAmount
        ) AS NetSales

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

Returns AS
(
    SELECT
        o.CustomerId,

        SUM(
            ri.ReturnedNetAmount
        ) AS Returns

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

SELECT TOP (20)

    c.CustomerCode,

    c.FirstName,
    c.LastName,

    c.Nationality,

    s.Orders,

    CAST(
        s.NetSales
        - COALESCE(
            r.Returns,
            0
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        (
            s.NetSales
            - COALESCE(
                r.Returns,
                0
            )
        )
        / NULLIF(
            s.Orders,
            0
        )
        AS DECIMAL(19,2)
    ) AS AOV

FROM Sales s

INNER JOIN customer.Customer c
    ON s.CustomerId
       = c.CustomerId

LEFT JOIN Returns r
    ON s.CustomerId
       = r.CustomerId

ORDER BY
    Revenue DESC;
GO


/* =========================================================
   5. CUSTOMER ORDER FREQUENCY DISTRIBUTION
   ========================================================= */

WITH CustomerOrders AS
(
    SELECT
        CustomerId,

        COUNT_BIG(*)
            AS Orders

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
),

Buckets AS
(
    SELECT
        CustomerId,

        CASE
            WHEN Orders = 1
                THEN '1 Order'

            WHEN Orders BETWEEN 2 AND 3
                THEN '2-3 Orders'

            WHEN Orders BETWEEN 4 AND 5
                THEN '4-5 Orders'

            WHEN Orders BETWEEN 6 AND 10
                THEN '6-10 Orders'

            ELSE
                '11+ Orders'
        END AS FrequencyBand

    FROM CustomerOrders
)

SELECT
    FrequencyBand,

    COUNT_BIG(*)
        AS Customers,

    CAST(
        COUNT_BIG(*)
        * 100.0
        /
        SUM(
            COUNT_BIG(*)
        ) OVER ()
        AS DECIMAL(10,2)
    ) AS CustomerPct

FROM Buckets

GROUP BY
    FrequencyBand

ORDER BY
    CASE FrequencyBand
        WHEN '1 Order'
            THEN 1
        WHEN '2-3 Orders'
            THEN 2
        WHEN '4-5 Orders'
            THEN 3
        WHEN '6-10 Orders'
            THEN 4
        ELSE 5
    END;
GO


/* =========================================================
   6. CUSTOMER REVENUE DISTRIBUTION

   Useful before RFM/Pareto analysis.
   ========================================================= */

WITH CustomerRevenue AS
(
    SELECT
        o.CustomerId,

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
                    ro.CustomerId
                    = o.CustomerId

                    AND r.ReturnStatus
                    = 'COMPLETED'
            ),
            0
        ) AS Revenue

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

Stats AS
(
    SELECT
        COUNT_BIG(*)
            AS PurchasingCustomers,

        AVG(
            Revenue
        ) AS MeanCustomerRevenue,

        MIN(
            Revenue
        ) AS MinimumCustomerRevenue,

        MAX(
            Revenue
        ) AS MaximumCustomerRevenue

    FROM CustomerRevenue
)

SELECT
    PurchasingCustomers,

    CAST(
        MeanCustomerRevenue
        AS DECIMAL(19,2)
    ) AS MeanCustomerRevenue,

    CAST(
        MinimumCustomerRevenue
        AS DECIMAL(19,2)
    ) AS MinimumCustomerRevenue,

    CAST(
        MaximumCustomerRevenue
        AS DECIMAL(19,2)
    ) AS MaximumCustomerRevenue

FROM Stats;
GO