"""
UAE Retail Intelligence Platform
Secure Customer Analytics Layer

Filtered and RLS-aware analytics for:
- Customer value
- RFM
- Segmentation
- Customer concentration
- Cohort retention
- Customer lifecycle
- Purchase frequency
- Monetary value

Security:
AuthenticatedUser
-> application permission
-> SESSION_CONTEXT(UserId)
-> SQL Server RLS
-> analytics.vw_SalesDetail

Important:
Customer analytics are calculated only from sales rows
visible to the authenticated user.

The unscoped analytics.vw_Customer360 view is intentionally
not used here because customer.Customer itself is not protected
by the store RLS policy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import (
    Connection,
    Engine,
)

from app.filters import DashboardFilters
from src.security.authentication import (
    AuthenticatedUser,
)
from src.security.session_context import (
    user_database_connection,
)


class CustomerPermissionError(
    PermissionError
):
    pass


# ============================================================
# Security
# ============================================================

def _require_customer_permission(
    user: AuthenticatedUser,
) -> None:
    if not isinstance(
        user,
        AuthenticatedUser,
    ):
        raise TypeError(
            "user must be an "
            "AuthenticatedUser."
        )

    allowed = (
        user.has_permission(
            "VIEW_CUSTOMERS"
        )
        or user.has_permission(
            "VIEW_RFM"
        )
    )

    if not allowed:
        raise CustomerPermissionError(
            "VIEW_CUSTOMERS or VIEW_RFM "
            "permission required."
        )


def _require_cohort_permission(
    user: AuthenticatedUser,
) -> None:
    _require_customer_permission(
        user
    )

    allowed = (
        user.has_permission(
            "VIEW_COHORTS"
        )
        or user.has_permission(
            "VIEW_CUSTOMERS"
        )
    )

    if not allowed:
        raise CustomerPermissionError(
            "VIEW_COHORTS or VIEW_CUSTOMERS "
            "permission required."
        )


# ============================================================
# SQL Helpers
# ============================================================

def _read_dataframe(
    connection: Connection,
    query: str,
    params: dict | None = None,
) -> pd.DataFrame:
    return pd.read_sql_query(
        text(query),
        connection,
        params=params or {},
    )


def _filter_sql(
    filters: DashboardFilters,
) -> tuple[str, dict]:
    conditions = [
        "1 = 1"
    ]

    params: dict = {}

    if filters.start_date is not None:
        conditions.append(
            "FullDate >= :customer_start_date"
        )

        params[
            "customer_start_date"
        ] = filters.start_date

    if filters.end_date is not None:
        conditions.append(
            "FullDate <= :customer_end_date"
        )

        params[
            "customer_end_date"
        ] = filters.end_date

    if filters.emirates:
        placeholders = []

        for index, emirate in enumerate(
            filters.emirates
        ):
            key = (
                f"customer_emirate_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = emirate

        conditions.append(
            "EmirateName IN "
            f"({', '.join(placeholders)})"
        )

    if filters.store_ids:
        placeholders = []

        for index, store_id in enumerate(
            filters.store_ids
        ):
            key = (
                f"customer_store_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = int(
                store_id
            )

        conditions.append(
            "StoreId IN "
            f"({', '.join(placeholders)})"
        )

    return (
        " AND ".join(
            conditions
        ),
        params,
    )


# ============================================================
# Customer Base
# ============================================================

def get_filtered_customer_metrics(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    """
    Grain:
    One row per customer with at least one completed
    purchase visible inside the current RLS + filter scope.

    This is a behavioral customer dataset, not the full
    registered customer master.
    """

    _require_customer_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        WITH CustomerMetrics AS
        (
            SELECT
                CustomerId,
                CustomerCode,

                MIN(FullDate)
                    AS FirstPurchaseDate,

                MAX(FullDate)
                    AS LastPurchaseDate,

                COUNT(
                    DISTINCT OrderId
                ) AS Orders,

                COUNT_BIG(*)
                    AS SalesLines,

                SUM(GrossUnits)
                    AS GrossUnits,

                SUM(ReturnedUnits)
                    AS ReturnedUnits,

                SUM(NetUnits)
                    AS NetUnits,

                SUM(GrossSales)
                    AS GrossSales,

                SUM(DiscountAmount)
                    AS DiscountAmount,

                SUM(Revenue)
                    AS Revenue,

                SUM(GrossProfit)
                    AS GrossProfit

            FROM analytics.vw_SalesDetail

            WHERE
                {where_clause}

            GROUP BY
                CustomerId,
                CustomerCode
        )

        SELECT
            *

        FROM CustomerMetrics

        ORDER BY
            Revenue DESC
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
            params,
        )

    if df.empty:
        return df

    df[
        "FirstPurchaseDate"
    ] = pd.to_datetime(
        df[
            "FirstPurchaseDate"
        ]
    )

    df[
        "LastPurchaseDate"
    ] = pd.to_datetime(
        df[
            "LastPurchaseDate"
        ]
    )

    df[
        "AOV"
    ] = np.where(
        df[
            "Orders"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "Orders"
        ],
        0,
    )

    df[
        "GrossMarginPct"
    ] = np.where(
        df[
            "Revenue"
        ] != 0,
        df[
            "GrossProfit"
        ]
        * 100.0
        / df[
            "Revenue"
        ],
        0,
    )

    df[
        "ReturnRatePct"
    ] = np.where(
        df[
            "GrossUnits"
        ] != 0,
        df[
            "ReturnedUnits"
        ]
        * 100.0
        / df[
            "GrossUnits"
        ],
        0,
    )

    df[
        "DiscountRatePct"
    ] = np.where(
        df[
            "GrossSales"
        ] != 0,
        df[
            "DiscountAmount"
        ]
        * 100.0
        / df[
            "GrossSales"
        ],
        0,
    )

    df[
        "UnitsPerOrder"
    ] = np.where(
        df[
            "Orders"
        ] != 0,
        df[
            "NetUnits"
        ]
        / df[
            "Orders"
        ],
        0,
    )

    df[
        "IsRepeatCustomer"
    ] = (
        df[
            "Orders"
        ]
        >= 2
    )

    return df


# ============================================================
# RFM
# ============================================================

def get_filtered_customer_rfm(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_customer_permission(
        user
    )

    customers = (
        get_filtered_customer_metrics(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if customers.empty:
        return customers

    data = customers.copy()

    # Reference date is the maximum purchase date visible
    # inside the current RLS + analytical filter scope.
    reference_date = (
        data[
            "LastPurchaseDate"
        ]
        .max()
    )

    data[
        "Recency"
    ] = (
        reference_date
        - data[
            "LastPurchaseDate"
        ]
    ).dt.days

    data[
        "Frequency"
    ] = data[
        "Orders"
    ]

    data[
        "Monetary"
    ] = data[
        "Revenue"
    ]

    customer_count = len(
        data
    )

    # --------------------------------------------------------
    # RFM scoring
    #
    # Rank before qcut so duplicate raw values do not cause
    # non-unique quantile boundaries.
    #
    # For tiny scopes (for example a highly filtered store /
    # date combination), fall back to percentile scoring.
    # --------------------------------------------------------

    if customer_count >= 5:
        data[
            "RScore"
        ] = pd.qcut(
            data[
                "Recency"
            ]
            .rank(
                method="first",
                ascending=True,
            ),
            5,
            labels=[
                5,
                4,
                3,
                2,
                1,
            ],
        ).astype(int)

        data[
            "FScore"
        ] = pd.qcut(
            data[
                "Frequency"
            ]
            .rank(
                method="first",
                ascending=True,
            ),
            5,
            labels=[
                1,
                2,
                3,
                4,
                5,
            ],
        ).astype(int)

        data[
            "MScore"
        ] = pd.qcut(
            data[
                "Monetary"
            ]
            .rank(
                method="first",
                ascending=True,
            ),
            5,
            labels=[
                1,
                2,
                3,
                4,
                5,
            ],
        ).astype(int)

    else:
        # Tiny-scope fallback.
        # Scores remain bounded 1..5.
        recency_rank = (
            data[
                "Recency"
            ]
            .rank(
                pct=True,
                ascending=False,
            )
        )

        frequency_rank = (
            data[
                "Frequency"
            ]
            .rank(
                pct=True,
                ascending=True,
            )
        )

        monetary_rank = (
            data[
                "Monetary"
            ]
            .rank(
                pct=True,
                ascending=True,
            )
        )

        data[
            "RScore"
        ] = np.clip(
            np.ceil(
                recency_rank
                * 5
            ),
            1,
            5,
        ).astype(int)

        data[
            "FScore"
        ] = np.clip(
            np.ceil(
                frequency_rank
                * 5
            ),
            1,
            5,
        ).astype(int)

        data[
            "MScore"
        ] = np.clip(
            np.ceil(
                monetary_rank
                * 5
            ),
            1,
            5,
        ).astype(int)

    data[
        "RFMScore"
    ] = (
        data[
            "RScore"
        ].astype(str)
        + data[
            "FScore"
        ].astype(str)
        + data[
            "MScore"
        ].astype(str)
    )

    data[
        "RFMTotal"
    ] = (
        data[
            "RScore"
        ]
        + data[
            "FScore"
        ]
        + data[
            "MScore"
        ]
    )

    def assign_segment(
        row,
    ) -> str:
        r = int(
            row[
                "RScore"
            ]
        )

        f = int(
            row[
                "FScore"
            ]
        )

        m = int(
            row[
                "MScore"
            ]
        )

        if (
            r >= 4
            and f >= 4
            and m >= 4
        ):
            return "Champions"

        if (
            r >= 3
            and f >= 4
        ):
            return "Loyal"

        if (
            r >= 4
            and f >= 2
            and m >= 2
        ):
            return "Potential Loyalists"

        if (
            r >= 4
            and f <= 2
        ):
            return "Promising"

        if (
            r <= 2
            and f >= 4
        ):
            return "At Risk"

        if (
            r <= 2
            and f <= 2
        ):
            return "Hibernating"

        return "Needs Attention"

    data[
        "Segment"
    ] = data.apply(
        assign_segment,
        axis=1,
    )

    # --------------------------------------------------------
    # Relative value tier
    # --------------------------------------------------------

    data[
        "ValueTier"
    ] = pd.cut(
        data[
            "MScore"
        ],
        bins=[
            0,
            2,
            3,
            5,
        ],
        labels=[
            "Low Value",
            "Medium Value",
            "High Value",
        ],
    )

    return (
        data.sort_values(
            [
                "RFMTotal",
                "Monetary",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# RFM Segment Summary
# ============================================================

def get_filtered_rfm_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    rfm = get_filtered_customer_rfm(
        user=user,
        filters=filters,
        engine=engine,
    )

    if rfm.empty:
        return pd.DataFrame()

    summary = (
        rfm.groupby(
            "Segment",
            as_index=False,
        )
        .agg(
            Customers=(
                "CustomerId",
                "count",
            ),

            Revenue=(
                "Monetary",
                "sum",
            ),

            GrossProfit=(
                "GrossProfit",
                "sum",
            ),

            AvgRecency=(
                "Recency",
                "mean",
            ),

            AvgFrequency=(
                "Frequency",
                "mean",
            ),

            AvgMonetary=(
                "Monetary",
                "mean",
            ),

            AvgAOV=(
                "AOV",
                "mean",
            ),

            AvgReturnRatePct=(
                "ReturnRatePct",
                "mean",
            ),
        )
    )

    total_customers = (
        summary[
            "Customers"
        ].sum()
    )

    total_revenue = (
        summary[
            "Revenue"
        ].sum()
    )

    summary[
        "CustomerSharePct"
    ] = (
        summary[
            "Customers"
        ]
        / total_customers
        * 100
        if total_customers
        else 0
    )

    summary[
        "RevenueSharePct"
    ] = (
        summary[
            "Revenue"
        ]
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    summary[
        "GrossMarginPct"
    ] = np.where(
        summary[
            "Revenue"
        ] != 0,
        summary[
            "GrossProfit"
        ]
        * 100
        / summary[
            "Revenue"
        ],
        0,
    )

    return (
        summary.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# Revenue Concentration
# ============================================================

def get_filtered_customer_concentration(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    customers = (
        get_filtered_customer_metrics(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if customers.empty:
        return customers

    data = (
        customers.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
        .copy()
    )

    total_revenue = float(
        data[
            "Revenue"
        ].sum()
    )

    data[
        "CustomerRank"
    ] = (
        data.index + 1
    )

    data[
        "CustomerPct"
    ] = (
        data[
            "CustomerRank"
        ]
        / len(data)
        * 100
    )

    data[
        "RevenueSharePct"
    ] = (
        data[
            "Revenue"
        ]
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    data[
        "CumulativeRevenuePct"
    ] = (
        data[
            "Revenue"
        ]
        .cumsum()
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    return data


# ============================================================
# Frequency Distribution
# ============================================================

def get_filtered_frequency_distribution(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    customers = (
        get_filtered_customer_metrics(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if customers.empty:
        return pd.DataFrame()

    data = customers.copy()

    data[
        "FrequencyBand"
    ] = pd.cut(
        data[
            "Orders"
        ],
        bins=[
            0,
            1,
            2,
            3,
            5,
            10,
            np.inf,
        ],
        labels=[
            "1 Order",
            "2 Orders",
            "3 Orders",
            "4-5 Orders",
            "6-10 Orders",
            "11+ Orders",
        ],
        include_lowest=True,
    )

    summary = (
        data.groupby(
            "FrequencyBand",
            observed=False,
            as_index=False,
        )
        .agg(
            Customers=(
                "CustomerId",
                "count",
            ),

            Revenue=(
                "Revenue",
                "sum",
            ),

            GrossProfit=(
                "GrossProfit",
                "sum",
            ),

            AvgAOV=(
                "AOV",
                "mean",
            ),
        )
    )

    return summary


# ============================================================
# Customer Lifecycle
# ============================================================

def get_filtered_customer_lifecycle(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    customers = (
        get_filtered_customer_metrics(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if customers.empty:
        return customers

    data = customers.copy()

    data[
        "CustomerLifetimeDays"
    ] = (
        data[
            "LastPurchaseDate"
        ]
        - data[
            "FirstPurchaseDate"
        ]
    ).dt.days

    data[
        "LifecycleStage"
    ] = np.select(
        [
            data[
                "Orders"
            ] == 1,

            (
                data[
                    "Orders"
                ]
                >= 2
            )
            & (
                data[
                    "Orders"
                ]
                <= 3
            ),

            (
                data[
                    "Orders"
                ]
                >= 4
            )
            & (
                data[
                    "Orders"
                ]
                <= 7
            ),

            data[
                "Orders"
            ] >= 8,
        ],
        [
            "One-Time",
            "Early Repeat",
            "Established",
            "High Frequency",
        ],
        default="Other",
    )

    return data


# ============================================================
# Monthly Customer Activity
# ============================================================

def get_filtered_monthly_customer_activity(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_customer_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        WITH CustomerMonth AS
        (
            SELECT
                DATEFROMPARTS(
                    YearNumber,
                    MonthNumber,
                    1
                ) AS MonthStart,

                CustomerId,

                COUNT(
                    DISTINCT OrderId
                ) AS Orders,

                SUM(Revenue)
                    AS Revenue,

                SUM(GrossProfit)
                    AS GrossProfit

            FROM analytics.vw_SalesDetail

            WHERE
                {where_clause}

            GROUP BY
                YearNumber,
                MonthNumber,
                CustomerId
        ),

        FirstVisibleMonth AS
        (
            SELECT
                CustomerId,

                MIN(MonthStart)
                    AS FirstMonth

            FROM CustomerMonth

            GROUP BY
                CustomerId
        )

        SELECT
            cm.MonthStart,

            COUNT(
                DISTINCT cm.CustomerId
            ) AS ActiveCustomers,

            COUNT(
                DISTINCT CASE
                    WHEN
                        cm.MonthStart
                        = fm.FirstMonth
                    THEN cm.CustomerId
                END
            ) AS NewCustomers,

            COUNT(
                DISTINCT CASE
                    WHEN
                        cm.MonthStart
                        > fm.FirstMonth
                    THEN cm.CustomerId
                END
            ) AS ReturningCustomers,

            SUM(cm.Orders)
                AS Orders,

            SUM(cm.Revenue)
                AS Revenue,

            SUM(cm.GrossProfit)
                AS GrossProfit

        FROM CustomerMonth cm

        INNER JOIN FirstVisibleMonth fm
            ON cm.CustomerId
               = fm.CustomerId

        GROUP BY
            cm.MonthStart

        ORDER BY
            cm.MonthStart
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
            params,
        )

    if df.empty:
        return df

    df[
        "MonthStart"
    ] = pd.to_datetime(
        df[
            "MonthStart"
        ]
    )

    df[
        "ReturningCustomerPct"
    ] = np.where(
        df[
            "ActiveCustomers"
        ] != 0,
        df[
            "ReturningCustomers"
        ]
        * 100.0
        / df[
            "ActiveCustomers"
        ],
        0,
    )

    df[
        "RevenuePerActiveCustomer"
    ] = np.where(
        df[
            "ActiveCustomers"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "ActiveCustomers"
        ],
        0,
    )

    return df


# ============================================================
# Cohort Retention
# ============================================================

def get_filtered_cohort_retention(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    """
    Cohorts are based on the first purchase visible within
    the current analytical scope.

    Therefore, when a date filter is active this is a
    scoped-window cohort analysis rather than an all-time
    acquisition cohort analysis.
    """

    _require_cohort_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        WITH Purchases AS
        (
            SELECT DISTINCT
                CustomerId,

                DATEFROMPARTS(
                    YearNumber,
                    MonthNumber,
                    1
                ) AS PurchaseMonth

            FROM analytics.vw_SalesDetail

            WHERE
                {where_clause}
        ),

        Cohorts AS
        (
            SELECT
                CustomerId,

                MIN(PurchaseMonth)
                    AS CohortMonth

            FROM Purchases

            GROUP BY
                CustomerId
        ),

        Activity AS
        (
            SELECT
                c.CohortMonth,

                p.PurchaseMonth,

                DATEDIFF(
                    MONTH,
                    c.CohortMonth,
                    p.PurchaseMonth
                ) AS CohortIndex,

                COUNT(
                    DISTINCT p.CustomerId
                ) AS ActiveCustomers

            FROM Purchases p

            INNER JOIN Cohorts c
                ON p.CustomerId
                   = c.CustomerId

            GROUP BY
                c.CohortMonth,
                p.PurchaseMonth,

                DATEDIFF(
                    MONTH,
                    c.CohortMonth,
                    p.PurchaseMonth
                )
        ),

        Sized AS
        (
            SELECT
                *,

                MAX(
                    CASE
                        WHEN
                            CohortIndex = 0
                        THEN
                            ActiveCustomers
                    END
                ) OVER
                (
                    PARTITION BY
                        CohortMonth
                ) AS CohortSize

            FROM Activity
        )

        SELECT
            CohortMonth,
            PurchaseMonth,
            CohortIndex,
            ActiveCustomers,
            CohortSize,

            ActiveCustomers
            * 100.0
            / NULLIF(
                CohortSize,
                0
            ) AS RetentionPct

        FROM Sized

        WHERE
            CohortIndex >= 0

        ORDER BY
            CohortMonth,
            CohortIndex
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
            params,
        )

    if df.empty:
        return df

    df[
        "CohortMonth"
    ] = pd.to_datetime(
        df[
            "CohortMonth"
        ]
    )

    df[
        "PurchaseMonth"
    ] = pd.to_datetime(
        df[
            "PurchaseMonth"
        ]
    )

    return df


# ============================================================
# Cohort Revenue
# ============================================================

def get_filtered_cohort_revenue(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_cohort_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        WITH CustomerMonth AS
        (
            SELECT
                CustomerId,

                DATEFROMPARTS(
                    YearNumber,
                    MonthNumber,
                    1
                ) AS PurchaseMonth,

                SUM(Revenue)
                    AS Revenue,

                SUM(GrossProfit)
                    AS GrossProfit

            FROM analytics.vw_SalesDetail

            WHERE
                {where_clause}

            GROUP BY
                CustomerId,
                YearNumber,
                MonthNumber
        ),

        Cohorts AS
        (
            SELECT
                CustomerId,

                MIN(PurchaseMonth)
                    AS CohortMonth

            FROM CustomerMonth

            GROUP BY
                CustomerId
        )

        SELECT
            c.CohortMonth,

            cm.PurchaseMonth,

            DATEDIFF(
                MONTH,
                c.CohortMonth,
                cm.PurchaseMonth
            ) AS CohortIndex,

            COUNT(
                DISTINCT cm.CustomerId
            ) AS ActiveCustomers,

            SUM(cm.Revenue)
                AS Revenue,

            SUM(cm.GrossProfit)
                AS GrossProfit

        FROM CustomerMonth cm

        INNER JOIN Cohorts c
            ON cm.CustomerId
               = c.CustomerId

        GROUP BY
            c.CohortMonth,
            cm.PurchaseMonth,

            DATEDIFF(
                MONTH,
                c.CohortMonth,
                cm.PurchaseMonth
            )

        ORDER BY
            c.CohortMonth,
            CohortIndex
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
            params,
        )

    if not df.empty:
        df[
            "CohortMonth"
        ] = pd.to_datetime(
            df[
                "CohortMonth"
            ]
        )

        df[
            "PurchaseMonth"
        ] = pd.to_datetime(
            df[
                "PurchaseMonth"
            ]
        )

    return df


# ============================================================
# Summary
# ============================================================

def get_filtered_customer_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> dict:
    customers = (
        get_filtered_customer_metrics(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if customers.empty:
        return {
            "Customers": 0,
            "RepeatCustomers": 0,
            "RepeatCustomerPct": 0.0,
            "Revenue": 0.0,
            "GrossProfit": 0.0,
            "Orders": 0,
            "AOV": 0.0,
            "RevenuePerCustomer": 0.0,
            "OrdersPerCustomer": 0.0,
            "ReturnRatePct": 0.0,
        }

    customer_count = len(
        customers
    )

    repeat_customers = int(
        customers[
            "IsRepeatCustomer"
        ].sum()
    )

    revenue = float(
        customers[
            "Revenue"
        ].sum()
    )

    profit = float(
        customers[
            "GrossProfit"
        ].sum()
    )

    orders = int(
        customers[
            "Orders"
        ].sum()
    )

    gross_units = float(
        customers[
            "GrossUnits"
        ].sum()
    )

    returned_units = float(
        customers[
            "ReturnedUnits"
        ].sum()
    )

    return {
        "Customers":
            customer_count,

        "RepeatCustomers":
            repeat_customers,

        "RepeatCustomerPct":
            (
                repeat_customers
                / customer_count
                * 100
                if customer_count
                else 0
            ),

        "Revenue":
            revenue,

        "GrossProfit":
            profit,

        "Orders":
            orders,

        "AOV":
            (
                revenue
                / orders
                if orders
                else 0
            ),

        "RevenuePerCustomer":
            (
                revenue
                / customer_count
                if customer_count
                else 0
            ),

        "OrdersPerCustomer":
            (
                orders
                / customer_count
                if customer_count
                else 0
            ),

        "ReturnRatePct":
            (
                returned_units
                / gross_units
                * 100
                if gross_units
                else 0
            ),
    }