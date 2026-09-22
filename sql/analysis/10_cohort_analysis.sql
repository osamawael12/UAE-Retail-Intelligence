/*
============================================================
 UAE Retail Intelligence Platform
 File: 10_cohort_analysis.sql

 Customer Cohort & Retention Analysis

 Cohort:
 Month of customer's first completed purchase.

 Retention:
 Percentage of original cohort customers purchasing again
 in Month N after acquisition.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. CUSTOMER FIRST PURCHASE / COHORT
   ========================================================= */

WITH FirstPurchase AS
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
)

SELECT
    c.CustomerCode,

    f.FirstPurchaseDate,

    DATEFROMPARTS(
        YEAR(
            f.FirstPurchaseDate
        ),
        MONTH(
            f.FirstPurchaseDate
        ),
        1
    ) AS CohortMonth

FROM FirstPurchase f

INNER JOIN customer.Customer c
    ON f.CustomerId
       = c.CustomerId

ORDER BY
    CohortMonth,
    c.CustomerCode;
GO


/* =========================================================
   2. COHORT SIZE
   ========================================================= */

WITH FirstPurchase AS
(
    SELECT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                MIN(
                    OrderDateTime
                )
            ),
            MONTH(
                MIN(
                    OrderDateTime
                )
            ),
            1
        ) AS CohortMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
)

SELECT
    CohortMonth,

    COUNT_BIG(*)
        AS CohortSize

FROM FirstPurchase

GROUP BY
    CohortMonth

ORDER BY
    CohortMonth;
GO


/* =========================================================
   3. COHORT RETENTION LONG FORMAT
   ========================================================= */

WITH FirstPurchase AS
(
    SELECT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                MIN(
                    OrderDateTime
                )
            ),
            MONTH(
                MIN(
                    OrderDateTime
                )
            ),
            1
        ) AS CohortMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
),

CustomerActivity AS
(
    SELECT DISTINCT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                OrderDateTime
            ),
            MONTH(
                OrderDateTime
            ),
            1
        ) AS ActivityMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'
),

CohortActivity AS
(
    SELECT
        f.CustomerId,
        f.CohortMonth,
        a.ActivityMonth,

        DATEDIFF(
            MONTH,
            f.CohortMonth,
            a.ActivityMonth
        ) AS CohortIndex

    FROM FirstPurchase f

    INNER JOIN CustomerActivity a
        ON f.CustomerId
           = a.CustomerId
),

CohortSize AS
(
    SELECT
        CohortMonth,

        COUNT_BIG(*)
            AS CohortSize

    FROM FirstPurchase

    GROUP BY
        CohortMonth
),

Retention AS
(
    SELECT
        CohortMonth,
        CohortIndex,

        COUNT_BIG(
            DISTINCT CustomerId
        ) AS ActiveCustomers

    FROM CohortActivity

    GROUP BY
        CohortMonth,
        CohortIndex
)

SELECT
    r.CohortMonth,
    r.CohortIndex,

    s.CohortSize,

    r.ActiveCustomers,

    CAST(
        r.ActiveCustomers
        * 100.0
        / NULLIF(
            s.CohortSize,
            0
        )
        AS DECIMAL(10,2)
    ) AS RetentionPct

FROM Retention r

INNER JOIN CohortSize s
    ON r.CohortMonth
       = s.CohortMonth

ORDER BY
    r.CohortMonth,
    r.CohortIndex;
GO


/* =========================================================
   4. COHORT RETENTION MATRIX

   Month 0 through Month 12.
   Ideal source for a heatmap in Python / Streamlit.
   ========================================================= */

WITH FirstPurchase AS
(
    SELECT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                MIN(
                    OrderDateTime
                )
            ),
            MONTH(
                MIN(
                    OrderDateTime
                )
            ),
            1
        ) AS CohortMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
),

Activity AS
(
    SELECT DISTINCT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                OrderDateTime
            ),
            MONTH(
                OrderDateTime
            ),
            1
        ) AS ActivityMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'
),

CohortActivity AS
(
    SELECT
        f.CustomerId,
        f.CohortMonth,

        DATEDIFF(
            MONTH,
            f.CohortMonth,
            a.ActivityMonth
        ) AS CohortIndex

    FROM FirstPurchase f

    INNER JOIN Activity a
        ON f.CustomerId
           = a.CustomerId
),

CohortSize AS
(
    SELECT
        CohortMonth,

        COUNT_BIG(*)
            AS CohortSize

    FROM FirstPurchase

    GROUP BY
        CohortMonth
),

Retention AS
(
    SELECT
        CohortMonth,
        CohortIndex,

        COUNT_BIG(
            DISTINCT CustomerId
        ) AS Customers

    FROM CohortActivity

    WHERE
        CohortIndex
        BETWEEN 0 AND 12

    GROUP BY
        CohortMonth,
        CohortIndex
),

Rates AS
(
    SELECT
        r.CohortMonth,
        r.CohortIndex,

        r.Customers
        * 100.0
        / NULLIF(
            s.CohortSize,
            0
        ) AS RetentionPct

    FROM Retention r

    INNER JOIN CohortSize s
        ON r.CohortMonth
           = s.CohortMonth
)

SELECT
    CohortMonth,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 0
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M0,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 1
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M1,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 2
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M2,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 3
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M3,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 4
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M4,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 5
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M5,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 6
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M6,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 7
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M7,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 8
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M8,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 9
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M9,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 10
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M10,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 11
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M11,

    CAST(
        MAX(
            CASE
                WHEN CohortIndex = 12
                    THEN RetentionPct
            END
        )
        AS DECIMAL(10,2)
    ) AS M12

FROM Rates

GROUP BY
    CohortMonth

ORDER BY
    CohortMonth;
GO


/* =========================================================
   5. COHORT REVENUE

   Revenue contribution by acquisition cohort.
   ========================================================= */

WITH FirstPurchase AS
(
    SELECT
        CustomerId,

        DATEFROMPARTS(
            YEAR(
                MIN(
                    OrderDateTime
                )
            ),
            MONTH(
                MIN(
                    OrderDateTime
                )
            ),
            1
        ) AS CohortMonth

    FROM sales.SalesOrder

    WHERE
        OrderStatus
        = 'COMPLETED'

    GROUP BY
        CustomerId
),

CustomerSales AS
(
    SELECT
        o.CustomerId,

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

CustomerReturns AS
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
),

CustomerRevenue AS
(
    SELECT
        f.CohortMonth,
        f.CustomerId,

        s.NetSales
        - COALESCE(
            r.Returns,
            0
        ) AS Revenue

    FROM FirstPurchase f

    INNER JOIN CustomerSales s
        ON f.CustomerId
           = s.CustomerId

    LEFT JOIN CustomerReturns r
        ON f.CustomerId
           = r.CustomerId
)

SELECT
    CohortMonth,

    COUNT_BIG(*)
        AS Customers,

    CAST(
        SUM(
            Revenue
        )
        AS DECIMAL(19,2)
    ) AS LifetimeRevenue,

    CAST(
        AVG(
            Revenue
        )
        AS DECIMAL(19,2)
    ) AS AvgLifetimeRevenuePerCustomer,

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
    ) AS RevenueContributionPct

FROM CustomerRevenue

GROUP BY
    CohortMonth

ORDER BY
    CohortMonth;
GO