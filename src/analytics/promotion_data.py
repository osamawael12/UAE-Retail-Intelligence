"""
UAE Retail Intelligence Platform
Secure Promotion Analytics Data Layer

Provides RLS-aware and analytical-filter-aware promotion
analytics for the Streamlit application.

Security path:
AuthenticatedUser
-> VIEW_SALES permission
-> SESSION_CONTEXT(UserId)
-> SQL Server Row-Level Security
-> analytical date/emirate/store filters
-> analytics.vw_SalesDetail

Important:
Promotion comparisons are descriptive associations.
They must not be interpreted as causal estimates of
incremental promotion lift.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import (
    Connection,
    Engine,
)

from app.filters import (
    DashboardFilters,
)
from src.security.authentication import (
    AuthenticatedUser,
)
from src.security.session_context import (
    user_database_connection,
)


class PromotionPermissionError(
    PermissionError
):
    pass


# ============================================================
# Security
# ============================================================

def _require_permission(
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

    if not user.has_permission(
        "VIEW_SALES"
    ):
        raise PromotionPermissionError(
            "VIEW_SALES permission required."
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
    filters: DashboardFilters | None,
) -> tuple[str, dict]:
    if filters is None:
        return (
            "1 = 1",
            {},
        )

    conditions = [
        "1 = 1"
    ]

    params: dict = {}

    if filters.start_date is not None:
        conditions.append(
            "FullDate >= :promo_start_date"
        )

        params[
            "promo_start_date"
        ] = filters.start_date

    if filters.end_date is not None:
        conditions.append(
            "FullDate <= :promo_end_date"
        )

        params[
            "promo_end_date"
        ] = filters.end_date

    if filters.emirates:
        placeholders = []

        for index, emirate in enumerate(
            filters.emirates
        ):
            key = (
                f"promo_emirate_{index}"
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
                f"promo_store_{index}"
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
# KPI Summary
# ============================================================

def get_promotion_kpis(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> dict:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            COUNT_BIG(*)
                AS SalesLines,

            SUM(
                CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN 1
                    ELSE 0
                END
            ) AS PromotedSalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN OrderId
                END
            ) AS PromotedOrders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            COUNT(
                DISTINCT CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN CustomerId
                END
            ) AS PromotionCustomers,

            COUNT(
                DISTINCT PromotionId
            ) AS PromotionsUsed,

            SUM(Revenue)
                AS Revenue,

            SUM(
                CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN Revenue
                    ELSE 0
                END
            ) AS PromotedRevenue,

            SUM(
                CASE
                    WHEN
                        PromotionId
                        IS NULL
                    THEN Revenue
                    ELSE 0
                END
            ) AS NonPromotedRevenue,

            SUM(GrossProfit)
                AS GrossProfit,

            SUM(
                CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN GrossProfit
                    ELSE 0
                END
            ) AS PromotedGrossProfit,

            SUM(GrossSales)
                AS GrossSales,

            SUM(DiscountAmount)
                AS DiscountAmount,

            SUM(
                CASE
                    WHEN
                        PromotionId
                        IS NOT NULL
                    THEN DiscountAmount
                    ELSE 0
                END
            ) AS PromotedDiscountAmount,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits

        FROM analytics.vw_SalesDetail

        WHERE
            {where_clause}
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        row = (
            connection.execute(
                text(query),
                params,
            )
            .mappings()
            .one()
        )

    result = dict(row)

    sales_lines = float(
        result[
            "SalesLines"
        ] or 0
    )

    promoted_lines = float(
        result[
            "PromotedSalesLines"
        ] or 0
    )

    orders = float(
        result[
            "Orders"
        ] or 0
    )

    promoted_orders = float(
        result[
            "PromotedOrders"
        ] or 0
    )

    customers = float(
        result[
            "Customers"
        ] or 0
    )

    promotion_customers = float(
        result[
            "PromotionCustomers"
        ] or 0
    )

    revenue = float(
        result[
            "Revenue"
        ] or 0
    )

    promoted_revenue = float(
        result[
            "PromotedRevenue"
        ] or 0
    )

    promoted_profit = float(
        result[
            "PromotedGrossProfit"
        ] or 0
    )

    gross_sales = float(
        result[
            "GrossSales"
        ] or 0
    )

    discount_amount = float(
        result[
            "DiscountAmount"
        ] or 0
    )

    gross_units = float(
        result[
            "GrossUnits"
        ] or 0
    )

    returned_units = float(
        result[
            "ReturnedUnits"
        ] or 0
    )

    result[
        "PromotionLineAdoptionPct"
    ] = (
        promoted_lines
        / sales_lines
        * 100
        if sales_lines
        else 0
    )

    result[
        "PromotionOrderAdoptionPct"
    ] = (
        promoted_orders
        / orders
        * 100
        if orders
        else 0
    )

    result[
        "PromotionCustomerPenetrationPct"
    ] = (
        promotion_customers
        / customers
        * 100
        if customers
        else 0
    )

    result[
        "PromotedRevenueSharePct"
    ] = (
        promoted_revenue
        / revenue
        * 100
        if revenue
        else 0
    )

    result[
        "PromotedGrossMarginPct"
    ] = (
        promoted_profit
        / promoted_revenue
        * 100
        if promoted_revenue
        else 0
    )

    result[
        "OverallDiscountRatePct"
    ] = (
        discount_amount
        / gross_sales
        * 100
        if gross_sales
        else 0
    )

    result[
        "OverallReturnRatePct"
    ] = (
        returned_units
        / gross_units
        * 100
        if gross_units
        else 0
    )

    return result


# ============================================================
# Promoted vs Non-Promoted
# ============================================================

def get_promotion_status_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            CASE
                WHEN
                    PromotionId
                    IS NULL
                THEN 'Non-Promoted'
                ELSE 'Promoted'
            END AS PromotionStatus,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

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
            CASE
                WHEN
                    PromotionId
                    IS NULL
                THEN 'Non-Promoted'
                ELSE 'Promoted'
            END
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
        "GrossMarginPct"
    ] = np.where(
        df[
            "Revenue"
        ] != 0,
        df[
            "GrossProfit"
        ]
        * 100
        / df[
            "Revenue"
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
        * 100
        / df[
            "GrossSales"
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
        * 100
        / df[
            "GrossUnits"
        ],
        0,
    )

    df[
        "RevenuePerLine"
    ] = np.where(
        df[
            "SalesLines"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "SalesLines"
        ],
        0,
    )

    df[
        "UnitsPerLine"
    ] = np.where(
        df[
            "SalesLines"
        ] != 0,
        df[
            "GrossUnits"
        ]
        / df[
            "SalesLines"
        ],
        0,
    )

    df[
        "RevenuePerOrder"
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

    return df


# ============================================================
# Promotion Types
# ============================================================

def get_promotion_type_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            PromotionType,

            COUNT(
                DISTINCT PromotionId
            ) AS Campaigns,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            PromotionType

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

    return _add_promotion_metrics(
        df
    )


# ============================================================
# Campaign Performance
# ============================================================

def get_campaign_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            PromotionId,
            PromotionCode,
            PromotionName,
            PromotionType,

            MIN(FullDate)
                AS FirstObservedDate,

            MAX(FullDate)
                AS LastObservedDate,

            COUNT(
                DISTINCT FullDate
            ) AS ActiveSalesDays,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            COUNT(
                DISTINCT StoreId
            ) AS Stores,

            COUNT(
                DISTINCT EmirateId
            ) AS Emirates,

            COUNT(
                DISTINCT ProductId
            ) AS Products,

            COUNT(
                DISTINCT CategoryId
            ) AS Categories,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            PromotionId,
            PromotionCode,
            PromotionName,
            PromotionType

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
        "FirstObservedDate"
    ] = pd.to_datetime(
        df[
            "FirstObservedDate"
        ]
    )

    df[
        "LastObservedDate"
    ] = pd.to_datetime(
        df[
            "LastObservedDate"
        ]
    )

    df = _add_promotion_metrics(
        df
    )

    df[
        "RevenuePerDay"
    ] = np.where(
        df[
            "ActiveSalesDays"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "ActiveSalesDays"
        ],
        0,
    )

    df[
        "RevenuePerCustomer"
    ] = np.where(
        df[
            "Customers"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "Customers"
        ],
        0,
    )

    # --------------------------------------------------------
    # Relative campaign score
    # --------------------------------------------------------

    revenue_score = (
        _min_max_score(
            df["Revenue"]
        )
    )

    profit_score = (
        _min_max_score(
            df[
                "GrossProfit"
            ]
        )
    )

    margin_score = (
        _min_max_score(
            df[
                "GrossMarginPct"
            ]
        )
    )

    customer_score = (
        _min_max_score(
            df[
                "Customers"
            ]
        )
    )

    return_health_score = (
        _min_max_score(
            df[
                "ReturnRatePct"
            ],
            reverse=True,
        )
    )

    discount_health_score = (
        _min_max_score(
            df[
                "DiscountRatePct"
            ],
            reverse=True,
        )
    )

    df[
        "CampaignScore"
    ] = (
        revenue_score
        * .25
        + profit_score
        * .25
        + margin_score
        * .15
        + customer_score
        * .10
        + return_health_score
        * .10
        + discount_health_score
        * .15
    )

    df[
        "CampaignScore"
    ] = (
        df[
            "CampaignScore"
        ]
        .clip(
            0,
            100,
        )
    )

    median_revenue = (
        df[
            "Revenue"
        ].median()
    )

    median_margin = (
        df[
            "GrossMarginPct"
        ].median()
    )

    low_margin = (
        df[
            "GrossMarginPct"
        ].quantile(
            .25
        )
    )

    high_returns = (
        df[
            "ReturnRatePct"
        ].quantile(
            .75
        )
    )

    high_discount = (
        df[
            "DiscountRatePct"
        ].quantile(
            .75
        )
    )

    df[
        "BusinessFlag"
    ] = np.select(
        [
            (
                df[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                df[
                    "GrossMarginPct"
                ]
                <= low_margin
            ),

            (
                df[
                    "ReturnRatePct"
                ]
                >= high_returns
            )
            & (
                df[
                    "GrossMarginPct"
                ]
                <= median_margin
            ),

            (
                df[
                    "DiscountRatePct"
                ]
                >= high_discount
            )
            & (
                df[
                    "GrossMarginPct"
                ]
                <= low_margin
            ),

            (
                df[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                df[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),
        ],
        [
            "High Revenue / Margin Pressure",
            "Return Risk",
            "Deep Discount / Margin Risk",
            "High Revenue / Healthy Margin",
        ],
        default="Normal",
    )

    df[
        "RevenueZScore"
    ] = _zscore(
        df[
            "Revenue"
        ]
    )

    df[
        "MarginZScore"
    ] = _zscore(
        df[
            "GrossMarginPct"
        ]
    )

    df[
        "ReturnZScore"
    ] = _zscore(
        df[
            "ReturnRatePct"
        ]
    )

    return (
        df.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# Discount Bands
# ============================================================

def get_discount_band_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        WITH Lines AS
        (
            SELECT
                OrderItemId,
                GrossUnits,
                ReturnedUnits,
                GrossSales,
                DiscountAmount,
                Revenue,
                GrossProfit,

                CASE
                    WHEN
                        GrossSales = 0
                        OR DiscountAmount = 0
                    THEN 'No Discount'

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 10
                    THEN '0-10%'

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 20
                    THEN '10-20%'

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 30
                    THEN '20-30%'

                    ELSE '30%+'
                END AS DiscountBand,

                CASE
                    WHEN
                        GrossSales = 0
                        OR DiscountAmount = 0
                    THEN 1

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 10
                    THEN 2

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 20
                    THEN 3

                    WHEN
                        DiscountAmount
                        * 100.0
                        / GrossSales
                        < 30
                    THEN 4

                    ELSE 5
                END AS BandOrder

            FROM analytics.vw_SalesDetail

            WHERE
                {where_clause}
        )

        SELECT
            DiscountBand,
            BandOrder,

            COUNT_BIG(*)
                AS SalesLines,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

            SUM(GrossSales)
                AS GrossSales,

            SUM(DiscountAmount)
                AS DiscountAmount,

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit

        FROM Lines

        GROUP BY
            DiscountBand,
            BandOrder

        ORDER BY
            BandOrder
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
        "GrossMarginPct"
    ] = np.where(
        df[
            "Revenue"
        ] != 0,
        df[
            "GrossProfit"
        ]
        * 100
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
        * 100
        / df[
            "GrossUnits"
        ],
        0,
    )

    df[
        "RevenuePerLine"
    ] = np.where(
        df[
            "SalesLines"
        ] != 0,
        df[
            "Revenue"
        ]
        / df[
            "SalesLines"
        ],
        0,
    )

    return df


# ============================================================
# Monthly Promotion Trend
# ============================================================

def get_monthly_promotion_trend(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            DATEFROMPARTS(
                YearNumber,
                MonthNumber,
                1
            ) AS MonthStart,

            CASE
                WHEN
                    PromotionId IS NULL
                THEN 'Non-Promoted'
                ELSE 'Promoted'
            END AS PromotionStatus,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            CASE
                WHEN
                    PromotionId IS NULL
                THEN 'Non-Promoted'
                ELSE 'Promoted'
            END

        ORDER BY
            MonthStart,
            PromotionStatus
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
        "GrossMarginPct"
    ] = np.where(
        df[
            "Revenue"
        ] != 0,
        df[
            "GrossProfit"
        ]
        * 100
        / df[
            "Revenue"
        ],
        0,
    )

    return df


# ============================================================
# Promotion Categories
# ============================================================

def get_promotion_category_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            CategoryId,
            CategoryName,

            COUNT(
                DISTINCT PromotionId
            ) AS Campaigns,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            CategoryId,
            CategoryName

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

    return _add_promotion_metrics(
        df
    )


# ============================================================
# Promotion Products
# ============================================================

def get_promotion_product_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            ProductId,
            SKU,
            ProductName,
            CategoryName,
            BrandName,

            COUNT(
                DISTINCT PromotionId
            ) AS Campaigns,

            COUNT_BIG(*)
                AS SalesLines,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            ProductId,
            SKU,
            ProductName,
            CategoryName,
            BrandName

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

    return _add_promotion_metrics(
        df
    )


# ============================================================
# Promotion Geography
# ============================================================

def get_promotion_emirate_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            EmirateId,
            EmirateName,

            COUNT(
                DISTINCT PromotionId
            ) AS Campaigns,

            COUNT(
                DISTINCT StoreId
            ) AS Stores,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            EmirateId,
            EmirateName

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

    return _add_promotion_metrics(
        df
    )


# ============================================================
# Promotion Store Performance
# ============================================================

def get_promotion_store_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(user)

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            StoreId,
            StoreCode,
            StoreName,
            EmirateName,

            COUNT(
                DISTINCT PromotionId
            ) AS Campaigns,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(GrossUnits)
                AS GrossUnits,

            SUM(ReturnedUnits)
                AS ReturnedUnits,

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

            AND PromotionId
                IS NOT NULL

        GROUP BY
            StoreId,
            StoreCode,
            StoreName,
            EmirateName

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

    return _add_promotion_metrics(
        df
    )


# ============================================================
# Seasonal Campaigns
# ============================================================

def get_seasonal_campaigns(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    campaigns = (
        get_campaign_performance(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if campaigns.empty:
        return campaigns

    return (
        campaigns.loc[
            campaigns[
                "PromotionType"
            ]
            == "SEASONAL"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


# ============================================================
# Seasonal Campaign Families
# ============================================================

def get_seasonal_campaign_family_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    seasonal = (
        get_seasonal_campaigns(
            user=user,
            filters=filters,
            engine=engine,
        )
    )

    if seasonal.empty:
        return pd.DataFrame()

    data = seasonal.copy()

    data[
        "CampaignFamily"
    ] = (
        data[
            "PromotionName"
        ]
        .str.replace(
            r"\s+\d{4}$",
            "",
            regex=True,
        )
    )

    summary = (
        data.groupby(
            "CampaignFamily",
            as_index=False,
        )
        .agg(
            Campaigns=(
                "PromotionId",
                "nunique",
            ),
            Orders=(
                "Orders",
                "sum",
            ),
            Customers=(
                "Customers",
                "sum",
            ),
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
            GrossSales=(
                "GrossSales",
                "sum",
            ),
            DiscountAmount=(
                "DiscountAmount",
                "sum",
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
            GrossProfit=(
                "GrossProfit",
                "sum",
            ),
        )
    )

    return _add_promotion_metrics(
        summary
    )


# ============================================================
# Shared Metrics
# ============================================================

def _add_promotion_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = dataframe.copy()

    if (
        "Revenue"
        in df.columns
        and "GrossProfit"
        in df.columns
    ):
        df[
            "GrossMarginPct"
        ] = np.where(
            df[
                "Revenue"
            ] != 0,
            df[
                "GrossProfit"
            ]
            * 100
            / df[
                "Revenue"
            ],
            0,
        )

    if (
        "GrossSales"
        in df.columns
        and "DiscountAmount"
        in df.columns
    ):
        df[
            "DiscountRatePct"
        ] = np.where(
            df[
                "GrossSales"
            ] != 0,
            df[
                "DiscountAmount"
            ]
            * 100
            / df[
                "GrossSales"
            ],
            0,
        )

    if (
        "GrossUnits"
        in df.columns
        and "ReturnedUnits"
        in df.columns
    ):
        df[
            "ReturnRatePct"
        ] = np.where(
            df[
                "GrossUnits"
            ] != 0,
            df[
                "ReturnedUnits"
            ]
            * 100
            / df[
                "GrossUnits"
            ],
            0,
        )

    if (
        "Revenue"
        in df.columns
        and "Orders"
        in df.columns
    ):
        df[
            "RevenuePerOrder"
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

    if (
        "Revenue"
        in df.columns
        and "Campaigns"
        in df.columns
    ):
        df[
            "RevenuePerCampaign"
        ] = np.where(
            df[
                "Campaigns"
            ] != 0,
            df[
                "Revenue"
            ]
            / df[
                "Campaigns"
            ],
            0,
        )

    return df


def _min_max_score(
    series: pd.Series,
    reverse: bool = False,
) -> pd.Series:
    values = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .fillna(0)
    )

    minimum = float(
        values.min()
    )

    maximum = float(
        values.max()
    )

    if maximum == minimum:
        score = pd.Series(
            np.full(
                len(values),
                50.0,
            ),
            index=values.index,
        )

    else:
        score = (
            (
                values
                - minimum
            )
            / (
                maximum
                - minimum
            )
            * 100
        )

    if reverse:
        score = (
            100 - score
        )

    return score


def _zscore(
    series: pd.Series,
) -> pd.Series:
    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    standard_deviation = (
        values.std(
            ddof=0
        )
    )

    if (
        pd.isna(
            standard_deviation
        )
        or standard_deviation == 0
    ):
        return pd.Series(
            np.zeros(
                len(values)
            ),
            index=values.index,
        )

    return (
        values
        - values.mean()
    ) / standard_deviation