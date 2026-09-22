/*
============================================================
 UAE Retail Intelligence Platform
 File: 09_rfm_analysis.sql

 RFM Customer Segmentation

 Reference Date:
 2025-12-31

 R = Recency
 F = Frequency
 M = Monetary

 Higher R score = more recent customer.
 Higher F score = more frequent customer.
 Higher M score = higher-value customer.

 Revenue excludes returned merchandise and VAT.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. CUSTOMER RFM VALUES
   ========================================================= */

WITH CustomerSales AS
(
    SELECT
        o.CustomerId,

        MAX(
            CAST(
                o.OrderDateTime
                AS DATE
            )
        ) AS LastPurchaseDate,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Frequency,

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
        ) AS ReturnedNetSales

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

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

    s.LastPurchaseDate,

    DATEDIFF(
        DAY,
        s.LastPurchaseDate,
        '2025-12-31'
    ) AS Recency,

    s.Frequency,

    CAST(
        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        )
        AS DECIMAL(19,2)
    ) AS Monetary

FROM CustomerSales s

INNER JOIN customer.Customer c
    ON s.CustomerId
       = c.CustomerId

LEFT JOIN CustomerReturns r
    ON s.CustomerId
       = r.CustomerId

ORDER BY
    Monetary DESC;
GO


/* =========================================================
   2. RFM SCORES

   NTILE(5):
   Recency uses DESC ordering because fewer days is better.

   Example:
   Recency = 5 days
   → High R Score

   Recency = 500 days
   → Low R Score
   ========================================================= */

WITH CustomerSales AS
(
    SELECT
        o.CustomerId,

        MAX(
            CAST(
                o.OrderDateTime
                AS DATE
            )
        ) AS LastPurchaseDate,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Frequency,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId
           = i.OrderId

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
        ON ri.ReturnId
           = r.ReturnId

    INNER JOIN sales.SalesOrderItem i
        ON ri.OrderItemId
           = i.OrderItemId

    INNER JOIN sales.SalesOrder o
        ON i.OrderId
           = o.OrderId

    WHERE
        r.ReturnStatus = 'COMPLETED'

    GROUP BY
        o.CustomerId
),

RFMValues AS
(
    SELECT
        s.CustomerId,

        DATEDIFF(
            DAY,
            s.LastPurchaseDate,
            '2025-12-31'
        ) AS Recency,

        s.Frequency,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Monetary

    FROM CustomerSales s

    LEFT JOIN CustomerReturns r
        ON s.CustomerId
           = r.CustomerId
),

RFMScores AS
(
    SELECT
        *,

        NTILE(5) OVER
        (
            ORDER BY
                Recency DESC
        ) AS RScore,

        NTILE(5) OVER
        (
            ORDER BY
                Frequency ASC
        ) AS FScore,

        NTILE(5) OVER
        (
            ORDER BY
                Monetary ASC
        ) AS MScore

    FROM RFMValues
)

SELECT
    c.CustomerCode,

    r.Recency,
    r.Frequency,

    CAST(
        r.Monetary
        AS DECIMAL(19,2)
    ) AS Monetary,

    r.RScore,
    r.FScore,
    r.MScore,

    CONCAT(
        r.RScore,
        r.FScore,
        r.MScore
    ) AS RFMCode

FROM RFMScores r

INNER JOIN customer.Customer c
    ON r.CustomerId
       = c.CustomerId

ORDER BY
    r.RScore DESC,
    r.FScore DESC,
    r.MScore DESC;
GO


/* =========================================================
   3. BUSINESS RFM SEGMENTATION
   ========================================================= */

WITH CustomerSales AS
(
    SELECT
        o.CustomerId,

        MAX(
            CAST(
                o.OrderDateTime
                AS DATE
            )
        ) AS LastPurchaseDate,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Frequency,

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
        ) AS ReturnedNetSales

    FROM sales.ReturnItem ri

    INNER JOIN sales.[Return] r
        ON ri.ReturnId = r.ReturnId

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

ValuesCTE AS
(
    SELECT
        s.CustomerId,

        DATEDIFF(
            DAY,
            s.LastPurchaseDate,
            '2025-12-31'
        ) AS Recency,

        s.Frequency,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Monetary

    FROM CustomerSales s

    LEFT JOIN CustomerReturns r
        ON s.CustomerId
           = r.CustomerId
),

Scores AS
(
    SELECT
        *,

        NTILE(5) OVER
        (
            ORDER BY
                Recency DESC
        ) AS RScore,

        NTILE(5) OVER
        (
            ORDER BY
                Frequency ASC
        ) AS FScore,

        NTILE(5) OVER
        (
            ORDER BY
                Monetary ASC
        ) AS MScore

    FROM ValuesCTE
),

Segments AS
(
    SELECT
        *,

        CASE
            WHEN
                RScore >= 4
                AND FScore >= 4
                AND MScore >= 4
                THEN 'Champions'

            WHEN
                RScore >= 3
                AND FScore >= 4
                THEN 'Loyal'

            WHEN
                RScore >= 4
                AND FScore BETWEEN 2 AND 3
                THEN 'Potential Loyalists'

            WHEN
                RScore = 5
                AND FScore = 1
                THEN 'New Customers'

            WHEN
                RScore <= 2
                AND FScore >= 3
                THEN 'At Risk'

            WHEN
                RScore = 1
                AND FScore <= 2
                THEN 'Lost'

            ELSE
                'Regular'
        END AS RFMSegment

    FROM Scores
)

SELECT
    c.CustomerCode,

    s.Recency,
    s.Frequency,

    CAST(
        s.Monetary
        AS DECIMAL(19,2)
    ) AS Monetary,

    s.RScore,
    s.FScore,
    s.MScore,

    s.RFMSegment

FROM Segments s

INNER JOIN customer.Customer c
    ON s.CustomerId
       = c.CustomerId

ORDER BY
    CASE s.RFMSegment
        WHEN 'Champions' THEN 1
        WHEN 'Loyal' THEN 2
        WHEN 'Potential Loyalists' THEN 3
        WHEN 'New Customers' THEN 4
        WHEN 'Regular' THEN 5
        WHEN 'At Risk' THEN 6
        WHEN 'Lost' THEN 7
        ELSE 8
    END,
    s.Monetary DESC;
GO


/* =========================================================
   4. RFM SEGMENT SUMMARY
   ========================================================= */

WITH CustomerSales AS
(
    SELECT
        o.CustomerId,

        MAX(
            CAST(
                o.OrderDateTime
                AS DATE
            )
        ) AS LastPurchaseDate,

        COUNT_BIG(
            DISTINCT o.OrderId
        ) AS Frequency,

        SUM(
            i.NetAmount
        ) AS NetSales

    FROM sales.SalesOrder o

    INNER JOIN sales.SalesOrderItem i
        ON o.OrderId = i.OrderId

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

ValuesCTE AS
(
    SELECT
        s.CustomerId,

        DATEDIFF(
            DAY,
            s.LastPurchaseDate,
            '2025-12-31'
        ) AS Recency,

        s.Frequency,

        s.NetSales
        - COALESCE(
            r.ReturnedNetSales,
            0
        ) AS Monetary

    FROM CustomerSales s

    LEFT JOIN CustomerReturns r
        ON s.CustomerId
           = r.CustomerId
),

Scores AS
(
    SELECT
        *,

        NTILE(5) OVER
        (
            ORDER BY
                Recency DESC
        ) AS RScore,

        NTILE(5) OVER
        (
            ORDER BY
                Frequency ASC
        ) AS FScore,

        NTILE(5) OVER
        (
            ORDER BY
                Monetary ASC
        ) AS MScore

    FROM ValuesCTE
),

Segments AS
(
    SELECT
        *,

        CASE
            WHEN
                RScore >= 4
                AND FScore >= 4
                AND MScore >= 4
                THEN 'Champions'

            WHEN
                RScore >= 3
                AND FScore >= 4
                THEN 'Loyal'

            WHEN
                RScore >= 4
                AND FScore BETWEEN 2 AND 3
                THEN 'Potential Loyalists'

            WHEN
                RScore = 5
                AND FScore = 1
                THEN 'New Customers'

            WHEN
                RScore <= 2
                AND FScore >= 3
                THEN 'At Risk'

            WHEN
                RScore = 1
                AND FScore <= 2
                THEN 'Lost'

            ELSE
                'Regular'
        END AS RFMSegment

    FROM Scores
)

SELECT
    RFMSegment,

    COUNT_BIG(*)
        AS Customers,

    CAST(
        COUNT_BIG(*)
        * 100.0
        / SUM(
            COUNT_BIG(*)
        ) OVER ()
        AS DECIMAL(10,2)
    ) AS CustomerPct,

    CAST(
        SUM(
            Monetary
        )
        AS DECIMAL(19,2)
    ) AS Revenue,

    CAST(
        SUM(
            Monetary
        )
        * 100.0
        / NULLIF(
            SUM(
                SUM(
                    Monetary
                )
            ) OVER (),
            0
        )
        AS DECIMAL(10,2)
    ) AS RevenueContributionPct,

    CAST(
        AVG(
            CAST(
                Recency
                AS DECIMAL(19,4)
            )
        )
        AS DECIMAL(10,2)
    ) AS AvgRecency,

    CAST(
        AVG(
            CAST(
                Frequency
                AS DECIMAL(19,4)
            )
        )
        AS DECIMAL(10,2)
    ) AS AvgFrequency,

    CAST(
        AVG(
            Monetary
        )
        AS DECIMAL(19,2)
    ) AS AvgCustomerRevenue

FROM Segments

GROUP BY
    RFMSegment

ORDER BY
    Revenue DESC;
GO