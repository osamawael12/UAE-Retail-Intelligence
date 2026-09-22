"""
UAE Retail Intelligence Platform
Secure Filtered Analytics Layer

Purpose:
- Apply analytical date / emirate / store filters in SQL.
- Keep SQL Server RLS as the actual security boundary.
- Provide filtered datasets for Streamlit dashboards.

Important:
Filters may only narrow visible data.
They are never used as an authorization mechanism.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

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


class FilterPermissionError(
    PermissionError
):
    pass


def _require_permission(
    user: AuthenticatedUser,
    permission: str,
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
        permission
    ):
        raise FilterPermissionError(
            "Permission required: "
            f"{permission}"
        )


def _require_any_permission(
    user: AuthenticatedUser,
    permissions: set[str],
) -> None:
    if not isinstance(
        user,
        AuthenticatedUser,
    ):
        raise TypeError(
            "user must be an "
            "AuthenticatedUser."
        )

    if not any(
        user.has_permission(
            permission
        )
        for permission
        in permissions
    ):
        raise FilterPermissionError(
            "One of these permissions "
            "is required: "
            + ", ".join(
                sorted(
                    permissions
                )
            )
        )


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
    date_column: str = "FullDate",
    emirate_column: str = "EmirateName",
    store_column: str = "StoreId",
) -> tuple[str, dict]:
    conditions = [
        "1 = 1"
    ]

    params: dict = {}

    if filters.start_date is not None:
        conditions.append(
            f"{date_column} >= :filter_start_date"
        )

        params[
            "filter_start_date"
        ] = filters.start_date

    if filters.end_date is not None:
        conditions.append(
            f"{date_column} <= :filter_end_date"
        )

        params[
            "filter_end_date"
        ] = filters.end_date

    if filters.emirates:
        placeholders = []

        for index, value in enumerate(
            filters.emirates
        ):
            key = (
                f"filter_emirate_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = value

        conditions.append(
            f"{emirate_column} IN "
            f"({', '.join(placeholders)})"
        )

    if filters.store_ids:
        placeholders = []

        for index, value in enumerate(
            filters.store_ids
        ):
            key = (
                f"filter_store_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = int(
                value
            )

        conditions.append(
            f"{store_column} IN "
            f"({', '.join(placeholders)})"
        )

    return (
        " AND ".join(
            conditions
        ),
        params,
    )


def get_filtered_summary(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> dict:
    _require_any_permission(
        user,
        {
            "VIEW_EXECUTIVE",
            "VIEW_SALES",
        },
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            COALESCE(
                SUM(Revenue),
                0
            ) AS Revenue,

            COALESCE(
                SUM(GrossProfit),
                0
            ) AS GrossProfit,

            CASE
                WHEN
                    COALESCE(
                        SUM(Revenue),
                        0
                    ) = 0
                    THEN 0
                ELSE
                    SUM(GrossProfit)
                    * 100.0
                    / SUM(Revenue)
            END AS GrossMarginPct,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            COALESCE(
                SUM(GrossUnits),
                0
            ) AS GrossUnits,

            COALESCE(
                SUM(ReturnedUnits),
                0
            ) AS ReturnedUnits,

            COALESCE(
                SUM(NetUnits),
                0
            ) AS NetUnits,

            CASE
                WHEN
                    COUNT(
                        DISTINCT OrderId
                    ) = 0
                    THEN 0
                ELSE
                    SUM(Revenue)
                    /
                    COUNT(
                        DISTINCT OrderId
                    )
            END AS AOV,

            CASE
                WHEN
                    COALESCE(
                        SUM(GrossUnits),
                        0
                    ) = 0
                    THEN 0
                ELSE
                    SUM(ReturnedUnits)
                    * 100.0
                    / SUM(GrossUnits)
            END AS ReturnRatePct

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

    return dict(row)


def get_filtered_daily_sales(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    where_clause, params = (
        _filter_sql(
            filters
        )
    )

    query = f"""
        SELECT
            FullDate,

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

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit

        FROM analytics.vw_SalesDetail

        WHERE
            {where_clause}

        GROUP BY
            FullDate

        ORDER BY
            FullDate
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        dataframe = _read_dataframe(
            connection,
            query,
            params,
        )

    if not dataframe.empty:
        dataframe[
            "FullDate"
        ] = pd.to_datetime(
            dataframe[
                "FullDate"
            ]
        )

        dataframe[
            "GrossMarginPct"
        ] = np.where(
            dataframe[
                "Revenue"
            ] != 0,
            dataframe[
                "GrossProfit"
            ]
            * 100.0
            / dataframe[
                "Revenue"
            ],
            0,
        )

        dataframe[
            "AOV"
        ] = np.where(
            dataframe[
                "Orders"
            ] != 0,
            dataframe[
                "Revenue"
            ]
            / dataframe[
                "Orders"
            ],
            0,
        )

    return dataframe


def get_filtered_monthly_sales(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

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

            YearNumber,
            MonthNumber,

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

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit

        FROM analytics.vw_SalesDetail

        WHERE
            {where_clause}

        GROUP BY
            YearNumber,
            MonthNumber

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

    df[
        "GrossMarginPct"
    ] = np.where(
        df["Revenue"] != 0,
        df["GrossProfit"]
        * 100.0
        / df["Revenue"],
        0,
    )

    df[
        "AOV"
    ] = np.where(
        df["Orders"] != 0,
        df["Revenue"]
        / df["Orders"],
        0,
    )

    df[
        "ReturnRatePct"
    ] = np.where(
        df["GrossUnits"] != 0,
        df["ReturnedUnits"]
        * 100.0
        / df["GrossUnits"],
        0,
    )

    df[
        "MoMRevenuePct"
    ] = (
        df["Revenue"]
        .pct_change(
            fill_method=None
        )
        .mul(100)
    )

    df[
        "YoYRevenuePct"
    ] = (
        df["Revenue"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    return df


def get_filtered_store_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_any_permission(
        user,
        {
            "VIEW_EXECUTIVE",
            "VIEW_STORES",
            "VIEW_SALES",
        },
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

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit,

            CASE
                WHEN SUM(Revenue) = 0
                    THEN 0
                ELSE
                    SUM(GrossProfit)
                    * 100.0
                    / SUM(Revenue)
            END AS GrossMarginPct,

            CASE
                WHEN
                    COUNT(
                        DISTINCT OrderId
                    ) = 0
                    THEN 0
                ELSE
                    SUM(Revenue)
                    /
                    COUNT(
                        DISTINCT OrderId
                    )
            END AS AOV,

            CASE
                WHEN SUM(GrossUnits) = 0
                    THEN 0
                ELSE
                    SUM(ReturnedUnits)
                    * 100.0
                    / SUM(GrossUnits)
            END AS ReturnRatePct

        FROM analytics.vw_SalesDetail

        WHERE
            {where_clause}

        GROUP BY
            StoreId,
            StoreCode,
            StoreName,
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

    if not df.empty:
        total = float(
            df["Revenue"].sum()
        )

        df[
            "RevenueSharePct"
        ] = (
            df["Revenue"]
            / total
            * 100.0
            if total
            else 0
        )

        df[
            "RevenueRank"
        ] = (
            df["Revenue"]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

    return df


def get_filtered_emirate_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_any_permission(
        user,
        {
            "VIEW_EXECUTIVE",
            "VIEW_STORES",
            "VIEW_SALES",
        },
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
                DISTINCT OrderId
            ) AS Orders,

            COUNT(
                DISTINCT CustomerId
            ) AS Customers,

            SUM(NetUnits)
                AS NetUnits,

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit,

            CASE
                WHEN SUM(Revenue) = 0
                    THEN 0
                ELSE
                    SUM(GrossProfit)
                    * 100.0
                    / SUM(Revenue)
            END AS GrossMarginPct

        FROM analytics.vw_SalesDetail

        WHERE
            {where_clause}

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
        return _read_dataframe(
            connection,
            query,
            params,
        )


def get_filtered_product_performance(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_PRODUCTS",
    )

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

            CategoryId,
            CategoryName,

            SubcategoryId,
            SubcategoryName,

            BrandId,
            BrandName,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

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
            ProductId,
            SKU,
            ProductName,
            CategoryId,
            CategoryName,
            SubcategoryId,
            SubcategoryName,
            BrandId,
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

    df[
        "GrossMarginPct"
    ] = np.where(
        df["Revenue"] != 0,
        df["GrossProfit"]
        * 100.0
        / df["Revenue"],
        0,
    )

    df[
        "ReturnRatePct"
    ] = np.where(
        df["GrossUnits"] != 0,
        df["ReturnedUnits"]
        * 100.0
        / df["GrossUnits"],
        0,
    )

    df[
        "DiscountDependencyPct"
    ] = np.where(
        df["GrossSales"] != 0,
        df["DiscountAmount"]
        * 100.0
        / df["GrossSales"],
        0,
    )

    total = float(
        df["Revenue"].sum()
    )

    df[
        "RevenueSharePct"
    ] = (
        df["Revenue"]
        / total
        * 100.0
        if total
        else 0
    )

    df[
        "CumulativeRevenuePct"
    ] = (
        df["Revenue"]
        .cumsum()
        / total
        * 100.0
        if total
        else 0
    )

    cumulative_before = (
        df[
            "CumulativeRevenuePct"
        ]
        - df[
            "RevenueSharePct"
        ]
    )

    df[
        "ABCClass"
    ] = np.select(
        [
            cumulative_before < 80,
            cumulative_before < 95,
        ],
        [
            "A",
            "B",
        ],
        default="C",
    )

    return df


def get_filtered_returns(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_RETURNS",
    )

    where_clause, params = (
        _filter_sql(
            filters,
            date_column="OrderDate",
            emirate_column="EmirateName",
            store_column="StoreId",
        )
    )

    query = f"""
        SELECT *
        FROM analytics.vw_ReturnAnalysis

        WHERE
            {where_clause}

        ORDER BY
            ReturnDateTime DESC
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

    for column in [
        "ReturnDateTime",
        "ReturnDate",
        "OrderDateTime",
        "OrderDate",
    ]:
        if column in df.columns:
            df[column] = (
                pd.to_datetime(
                    df[column]
                )
            )

    return df


def get_filtered_inventory(
    user: AuthenticatedUser,
    filters: DashboardFilters,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_INVENTORY",
    )

    conditions = [
        "1 = 1"
    ]

    params: dict = {}

    if filters.emirates:
        placeholders = []

        for index, value in enumerate(
            filters.emirates
        ):
            key = (
                f"inventory_emirate_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = value

        conditions.append(
            "EmirateName IN "
            f"({', '.join(placeholders)})"
        )

    if filters.store_ids:
        placeholders = []

        for index, value in enumerate(
            filters.store_ids
        ):
            key = (
                f"inventory_store_{index}"
            )

            placeholders.append(
                f":{key}"
            )

            params[key] = int(
                value
            )

        conditions.append(
            "StoreId IN "
            f"({', '.join(placeholders)})"
        )

    query = f"""
        SELECT *
        FROM analytics.vw_InventoryStatus

        WHERE
            {' AND '.join(conditions)}

        ORDER BY
            StoreCode,
            SKU
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

    if (
        "LastSaleDate"
        in df.columns
    ):
        df[
            "LastSaleDate"
        ] = pd.to_datetime(
            df[
                "LastSaleDate"
            ]
        )

    return df