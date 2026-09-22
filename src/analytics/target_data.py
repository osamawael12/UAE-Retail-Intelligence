"""
UAE Retail Intelligence Platform
Secure Target Analytics Data Layer

Purpose:
- Revenue target analytics
- Gross profit target analytics
- Order target analytics
- Monthly target trends
- Store target performance
- Emirate target performance

Security path:
AuthenticatedUser
-> VIEW_TARGETS permission
-> SESSION_CONTEXT(UserId)
-> SQL Server Row-Level Security
-> analytical filters
-> analytics.vw_TargetPerformance

Target grain:
Store x Month
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


class TargetPermissionError(
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
        "VIEW_TARGETS"
    ):
        raise TargetPermissionError(
            "VIEW_TARGETS permission required."
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

    # --------------------------------------------------------
    # Date semantics
    #
    # Targets are monthly.
    # A date range is translated into overlapping target
    # months using MonthStart.
    #
    # Example:
    # 2025-03-15 through 2025-07-10
    # includes target months March through July.
    # --------------------------------------------------------

    if filters.start_date is not None:
        conditions.append(
            """
            MonthStart
            >= DATEFROMPARTS(
                YEAR(:target_start_date),
                MONTH(:target_start_date),
                1
            )
            """
        )

        params[
            "target_start_date"
        ] = filters.start_date

    if filters.end_date is not None:
        conditions.append(
            """
            MonthStart
            <= DATEFROMPARTS(
                YEAR(:target_end_date),
                MONTH(:target_end_date),
                1
            )
            """
        )

        params[
            "target_end_date"
        ] = filters.end_date

    if filters.emirates:
        placeholders = []

        for index, emirate in enumerate(
            filters.emirates
        ):
            key = (
                f"target_emirate_{index}"
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
                f"target_store_{index}"
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
# Shared Calculated Metrics
# ============================================================

def _add_target_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = dataframe.copy()

    if df.empty:
        return df

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if {
        "ActualRevenue",
        "RevenueTarget",
    }.issubset(
        df.columns
    ):
        df[
            "RevenueVariance"
        ] = (
            df[
                "ActualRevenue"
            ]
            - df[
                "RevenueTarget"
            ]
        )

        df[
            "RevenueAchievementPct"
        ] = np.where(
            df[
                "RevenueTarget"
            ] != 0,
            df[
                "ActualRevenue"
            ]
            * 100.0
            / df[
                "RevenueTarget"
            ],
            np.nan,
        )

        df[
            "RevenueVariancePct"
        ] = np.where(
            df[
                "RevenueTarget"
            ] != 0,
            df[
                "RevenueVariance"
            ]
            * 100.0
            / df[
                "RevenueTarget"
            ],
            np.nan,
        )

    # --------------------------------------------------------
    # Gross Profit
    # --------------------------------------------------------

    if {
        "ActualGrossProfit",
        "GrossProfitTarget",
    }.issubset(
        df.columns
    ):
        df[
            "ProfitVariance"
        ] = (
            df[
                "ActualGrossProfit"
            ]
            - df[
                "GrossProfitTarget"
            ]
        )

        df[
            "ProfitAchievementPct"
        ] = np.where(
            df[
                "GrossProfitTarget"
            ] != 0,
            df[
                "ActualGrossProfit"
            ]
            * 100.0
            / df[
                "GrossProfitTarget"
            ],
            np.nan,
        )

        df[
            "ProfitVariancePct"
        ] = np.where(
            df[
                "GrossProfitTarget"
            ] != 0,
            df[
                "ProfitVariance"
            ]
            * 100.0
            / df[
                "GrossProfitTarget"
            ],
            np.nan,
        )

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    if {
        "ActualOrders",
        "OrdersTarget",
    }.issubset(
        df.columns
    ):
        df[
            "OrdersVariance"
        ] = (
            df[
                "ActualOrders"
            ]
            - df[
                "OrdersTarget"
            ]
        )

        df[
            "OrdersAchievementPct"
        ] = np.where(
            df[
                "OrdersTarget"
            ] != 0,
            df[
                "ActualOrders"
            ]
            * 100.0
            / df[
                "OrdersTarget"
            ],
            np.nan,
        )

        df[
            "OrdersVariancePct"
        ] = np.where(
            df[
                "OrdersTarget"
            ] != 0,
            df[
                "OrdersVariance"
            ]
            * 100.0
            / df[
                "OrdersTarget"
            ],
            np.nan,
        )

    return df


# ============================================================
# Detailed Target Performance
# ============================================================

def get_filtered_target_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            StoreMonthlyTargetId,

            StoreId,
            StoreCode,
            StoreName,

            EmirateId,
            EmirateName,

            TargetYear,
            TargetMonth,
            MonthStart,

            ActualRevenue,
            RevenueTarget,

            ActualGrossProfit,
            GrossProfitTarget,

            ActualOrders,
            OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        ORDER BY
            MonthStart,
            StoreCode
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Overall KPI Summary
# ============================================================

def get_filtered_target_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> dict:
    _require_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            COUNT_BIG(*)
                AS TargetRecords,

            COUNT(
                DISTINCT StoreId
            ) AS Stores,

            COUNT(
                DISTINCT EmirateId
            ) AS Emirates,

            COUNT(
                DISTINCT MonthStart
            ) AS Months,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

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

    result = dict(
        row
    )

    actual_revenue = float(
        result[
            "ActualRevenue"
        ] or 0
    )

    revenue_target = float(
        result[
            "RevenueTarget"
        ] or 0
    )

    actual_profit = float(
        result[
            "ActualGrossProfit"
        ] or 0
    )

    profit_target = float(
        result[
            "GrossProfitTarget"
        ] or 0
    )

    actual_orders = float(
        result[
            "ActualOrders"
        ] or 0
    )

    orders_target = float(
        result[
            "OrdersTarget"
        ] or 0
    )

    result[
        "RevenueVariance"
    ] = (
        actual_revenue
        - revenue_target
    )

    result[
        "RevenueAchievementPct"
    ] = (
        actual_revenue
        / revenue_target
        * 100
        if revenue_target
        else 0
    )

    result[
        "ProfitVariance"
    ] = (
        actual_profit
        - profit_target
    )

    result[
        "ProfitAchievementPct"
    ] = (
        actual_profit
        / profit_target
        * 100
        if profit_target
        else 0
    )

    result[
        "OrdersVariance"
    ] = (
        actual_orders
        - orders_target
    )

    result[
        "OrdersAchievementPct"
    ] = (
        actual_orders
        / orders_target
        * 100
        if orders_target
        else 0
    )

    return result


# ============================================================
# Monthly Performance
# ============================================================

def get_filtered_monthly_targets(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            MonthStart,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        GROUP BY
            MonthStart

        ORDER BY
            MonthStart
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Store Performance
# ============================================================

def get_filtered_store_targets(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

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

            EmirateId,
            EmirateName,

            COUNT(
                DISTINCT MonthStart
            ) AS Months,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        GROUP BY
            StoreId,
            StoreCode,
            StoreName,
            EmirateId,
            EmirateName

        ORDER BY
            ActualRevenue DESC
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Emirate Performance
# ============================================================

def get_filtered_emirate_targets(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

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
                DISTINCT StoreId
            ) AS Stores,

            COUNT(
                DISTINCT MonthStart
            ) AS Months,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        GROUP BY
            EmirateId,
            EmirateName

        ORDER BY
            ActualRevenue DESC
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Store x Month Performance
# ============================================================

def get_filtered_store_month_targets(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            MonthStart,

            StoreId,
            StoreCode,
            StoreName,

            EmirateId,
            EmirateName,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        GROUP BY
            MonthStart,
            StoreId,
            StoreCode,
            StoreName,
            EmirateId,
            EmirateName

        ORDER BY
            MonthStart,
            StoreCode
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Annual Performance
# ============================================================

def get_filtered_annual_targets(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            TargetYear,

            COUNT(
                DISTINCT StoreId
            ) AS Stores,

            SUM(ActualRevenue)
                AS ActualRevenue,

            SUM(RevenueTarget)
                AS RevenueTarget,

            SUM(ActualGrossProfit)
                AS ActualGrossProfit,

            SUM(GrossProfitTarget)
                AS GrossProfitTarget,

            SUM(ActualOrders)
                AS ActualOrders,

            SUM(OrdersTarget)
                AS OrdersTarget

        FROM analytics.vw_TargetPerformance

        WHERE
            {where_clause}

        GROUP BY
            TargetYear

        ORDER BY
            TargetYear
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

    return _add_target_metrics(
        df
    )


# ============================================================
# Achievement Distribution
# ============================================================

def get_target_achievement_distribution(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    stores = get_filtered_store_targets(
        user=user,
        filters=filters,
        engine=engine,
    )

    if stores.empty:
        return pd.DataFrame()

    data = stores.copy()

    data[
        "AchievementBand"
    ] = pd.cut(
        data[
            "RevenueAchievementPct"
        ],
        bins=[
            -np.inf,
            80,
            90,
            100,
            110,
            np.inf,
        ],
        labels=[
            "<80%",
            "80-90%",
            "90-100%",
            "100-110%",
            "110%+",
        ],
    )

    summary = (
        data.groupby(
            "AchievementBand",
            observed=False,
            as_index=False,
        )
        .agg(
            Stores=(
                "StoreId",
                "count",
            ),
            ActualRevenue=(
                "ActualRevenue",
                "sum",
            ),
            RevenueTarget=(
                "RevenueTarget",
                "sum",
            ),
            RevenueVariance=(
                "RevenueVariance",
                "sum",
            ),
        )
    )

    return summary


# ============================================================
# Underperformers
# ============================================================

def get_target_underperformers(
    user: AuthenticatedUser,
    filters: DashboardFilters | None = None,
    engine: Engine | None = None,
    threshold_pct: float = 90.0,
) -> pd.DataFrame:
    stores = get_filtered_store_targets(
        user=user,
        filters=filters,
        engine=engine,
    )

    if stores.empty:
        return stores

    result = (
        stores.loc[
            stores[
                "RevenueAchievementPct"
            ]
            < threshold_pct
        ]
        .sort_values(
            [
                "RevenueAchievementPct",
                "RevenueVariance",
            ],
            ascending=[
                True,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# Composite Performance Scoring
# ============================================================

def add_target_performance_score(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Relative management score.

    This is not an official financial KPI.
    It is intended only for dashboard prioritization.

    Components:
    - Revenue achievement: 45%
    - Profit achievement: 35%
    - Orders achievement: 20%

    Achievement is capped at 120 for scoring so extreme
    overperformance cannot dominate the relative score.
    """

    df = dataframe.copy()

    if df.empty:
        return df

    revenue_component = (
        pd.to_numeric(
            df[
                "RevenueAchievementPct"
            ],
            errors="coerce",
        )
        .fillna(0)
        .clip(
            lower=0,
            upper=120,
        )
        / 120
        * 100
    )

    profit_component = (
        pd.to_numeric(
            df[
                "ProfitAchievementPct"
            ],
            errors="coerce",
        )
        .fillna(0)
        .clip(
            lower=0,
            upper=120,
        )
        / 120
        * 100
    )

    orders_component = (
        pd.to_numeric(
            df[
                "OrdersAchievementPct"
            ],
            errors="coerce",
        )
        .fillna(0)
        .clip(
            lower=0,
            upper=120,
        )
        / 120
        * 100
    )

    df[
        "PerformanceScore"
    ] = (
        revenue_component
        * .45
        + profit_component
        * .35
        + orders_component
        * .20
    )

    df[
        "PerformanceTier"
    ] = pd.cut(
        df[
            "PerformanceScore"
        ],
        bins=[
            -np.inf,
            65,
            80,
            92,
            np.inf,
        ],
        labels=[
            "Priority Review",
            "Developing",
            "Strong",
            "Leading",
        ],
    )

    df[
        "TargetStatus"
    ] = np.select(
        [
            (
                df[
                    "RevenueAchievementPct"
                ]
                >= 100
            )
            & (
                df[
                    "ProfitAchievementPct"
                ]
                >= 100
            )
            & (
                df[
                    "OrdersAchievementPct"
                ]
                >= 100
            ),

            (
                df[
                    "RevenueAchievementPct"
                ]
                >= 100
            )
            & (
                df[
                    "ProfitAchievementPct"
                ]
                < 100
            ),

            (
                df[
                    "RevenueAchievementPct"
                ]
                < 90
            )
            | (
                df[
                    "ProfitAchievementPct"
                ]
                < 90
            ),

            (
                df[
                    "RevenueAchievementPct"
                ]
                >= 90
            )
            & (
                df[
                    "RevenueAchievementPct"
                ]
                < 100
            ),
        ],
        [
            "All Targets Achieved",
            "Revenue Achieved / Profit Gap",
            "Material Underperformance",
            "Near Target",
        ],
        default="Mixed Performance",
    )

    return df