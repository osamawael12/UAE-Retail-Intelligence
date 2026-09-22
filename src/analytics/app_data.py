"""
UAE Retail Intelligence Platform
Secure Application Analytics Data Layer

All interactive business-data access is:
Authenticated User
-> Permission Check
-> SESSION_CONTEXT(UserId)
-> SQL Server RLS
-> Analytics Views
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import (
    Connection,
    Engine,
)

from src.security.authentication import (
    AuthenticatedUser,
)
from src.security.session_context import (
    user_database_connection,
)


class PermissionDeniedError(
    PermissionError
):
    pass


def _require_user(
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


def _require_permission(
    user: AuthenticatedUser,
    permission: str,
) -> None:
    _require_user(user)

    if not user.has_permission(
        permission
    ):
        raise PermissionDeniedError(
            "Permission required: "
            f"{permission}"
        )


def _require_any_permission(
    user: AuthenticatedUser,
    permissions: set[str],
) -> None:
    _require_user(user)

    if not any(
        user.has_permission(permission)
        for permission in permissions
    ):
        raise PermissionDeniedError(
            "One of these permissions "
            "is required: "
            + ", ".join(
                sorted(permissions)
            )
        )


def _read_dataframe(
    connection: Connection,
    sql: str,
    params: dict | None = None,
) -> pd.DataFrame:
    return pd.read_sql_query(
        text(sql),
        connection,
        params=params or {},
    )


def _date_range(
    start_date: date | str | None,
    end_date: date | str | None,
):
    start = (
        pd.Timestamp(start_date)
        if start_date is not None
        else None
    )

    end = (
        pd.Timestamp(end_date)
        if end_date is not None
        else None
    )

    if (
        start is not None
        and end is not None
        and start > end
    ):
        raise ValueError(
            "start_date cannot be "
            "after end_date."
        )

    return (
        start.date()
        if start is not None
        else None,
        end.date()
        if end is not None
        else None,
    )


def get_visible_stores(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_user(user)

    query = """
        SELECT
            s.StoreId,
            s.StoreCode,
            s.StoreName,
            e.EmirateId,
            e.EmirateName

        FROM core.Store s

        INNER JOIN core.City c
            ON s.CityId = c.CityId

        INNER JOIN core.Emirate e
            ON c.EmirateId
               = e.EmirateId

        ORDER BY
            e.EmirateName,
            s.StoreCode
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        return _read_dataframe(
            connection,
            query,
        )


def get_data_bounds(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> dict:
    _require_any_permission(
        user,
        {
            "VIEW_EXECUTIVE",
            "VIEW_SALES",
            "VIEW_STORES",
            "VIEW_PRODUCTS",
        },
    )

    query = """
        SELECT
            MIN(FullDate) AS MinDate,
            MAX(FullDate) AS MaxDate
        FROM analytics.vw_SalesDetail
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        row = (
            connection.execute(
                text(query)
            )
            .mappings()
            .one()
        )

    return dict(row)


def get_executive_summary(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> dict:
    _require_permission(
        user,
        "VIEW_EXECUTIVE",
    )

    query = """
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
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        dataframe = _read_dataframe(
            connection,
            query,
        )

    return (
        dataframe.iloc[0]
        .to_dict()
    )


def get_daily_sales(
    user: AuthenticatedUser,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    start, end = _date_range(
        start_date,
        end_date,
    )

    conditions = ["1 = 1"]
    parameters = {}

    if start is not None:
        conditions.append(
            "FullDate >= :start_date"
        )
        parameters[
            "start_date"
        ] = start

    if end is not None:
        conditions.append(
            "FullDate <= :end_date"
        )
        parameters[
            "end_date"
        ] = end

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
            {' AND '.join(conditions)}

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
            parameters,
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
            dataframe["Revenue"] != 0,
            dataframe["GrossProfit"]
            * 100.0
            / dataframe["Revenue"],
            0,
        )

        dataframe[
            "AOV"
        ] = np.where(
            dataframe["Orders"] != 0,
            dataframe["Revenue"]
            / dataframe["Orders"],
            0,
        )

    return dataframe


def get_monthly_sales(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
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
        )

    if df.empty:
        return df

    df[
        "MonthStart"
    ] = pd.to_datetime(
        df["MonthStart"]
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


def get_annual_sales(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
        SELECT
            YearNumber,

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

        GROUP BY
            YearNumber

        ORDER BY
            YearNumber
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
        )

    if not df.empty:
        df["YoYRevenuePct"] = (
            df["Revenue"]
            .pct_change(
                fill_method=None
            )
            .mul(100)
        )

        df["GrossMarginPct"] = (
            np.where(
                df["Revenue"] != 0,
                df["GrossProfit"]
                * 100.0
                / df["Revenue"],
                0,
            )
        )

    return df


def get_ytd_comparison(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> dict:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
        WITH Bounds AS
        (
            SELECT
                MAX(FullDate)
                    AS MaxDate
            FROM analytics.vw_SalesDetail
        )

        SELECT
            b.MaxDate,

            SUM(
                CASE
                    WHEN
                        YEAR(s.FullDate)
                        = YEAR(b.MaxDate)

                        AND s.FullDate
                            <= b.MaxDate

                    THEN s.Revenue
                    ELSE 0
                END
            ) AS CurrentYTD,

            SUM(
                CASE
                    WHEN
                        YEAR(s.FullDate)
                        =
                        YEAR(b.MaxDate) - 1

                        AND
                        (
                            MONTH(s.FullDate)
                            <
                            MONTH(b.MaxDate)

                            OR
                            (
                                MONTH(s.FullDate)
                                =
                                MONTH(b.MaxDate)

                                AND
                                DAY(s.FullDate)
                                <=
                                DAY(b.MaxDate)
                            )
                        )

                    THEN s.Revenue
                    ELSE 0
                END
            ) AS PreviousYTD,

            SUM(
                CASE
                    WHEN
                        YEAR(s.FullDate)
                        = YEAR(b.MaxDate)

                        AND s.FullDate
                            <= b.MaxDate

                    THEN s.GrossProfit
                    ELSE 0
                END
            ) AS CurrentYTDProfit,

            SUM(
                CASE
                    WHEN
                        YEAR(s.FullDate)
                        =
                        YEAR(b.MaxDate) - 1

                        AND
                        (
                            MONTH(s.FullDate)
                            <
                            MONTH(b.MaxDate)

                            OR
                            (
                                MONTH(s.FullDate)
                                =
                                MONTH(b.MaxDate)

                                AND
                                DAY(s.FullDate)
                                <=
                                DAY(b.MaxDate)
                            )
                        )

                    THEN s.GrossProfit
                    ELSE 0
                END
            ) AS PreviousYTDProfit

        FROM analytics.vw_SalesDetail s

        CROSS JOIN Bounds b

        GROUP BY
            b.MaxDate
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
        )

    result = (
        df.iloc[0]
        .to_dict()
    )

    previous = float(
        result[
            "PreviousYTD"
        ] or 0
    )

    current = float(
        result[
            "CurrentYTD"
        ] or 0
    )

    result[
        "YTDGrowthPct"
    ] = (
        (
            current - previous
        )
        / abs(previous)
        * 100.0
        if previous
        else None
    )

    previous_profit = float(
        result[
            "PreviousYTDProfit"
        ] or 0
    )

    current_profit = float(
        result[
            "CurrentYTDProfit"
        ] or 0
    )

    result[
        "YTDProfitGrowthPct"
    ] = (
        (
            current_profit
            - previous_profit
        )
        / abs(previous_profit)
        * 100.0
        if previous_profit
        else None
    )

    return result


def get_sales_by_emirate(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_any_permission(
        user,
        {
            "VIEW_EXECUTIVE",
            "VIEW_SALES",
            "VIEW_STORES",
        },
    )

    query = """
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
        )


def get_sales_by_channel(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
        SELECT
            ChannelCode,
            ChannelName,

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
                AS GrossProfit

        FROM analytics.vw_SalesDetail

        GROUP BY
            ChannelCode,
            ChannelName

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
        )


def get_sales_seasonality(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
        SELECT
            MonthNumber,
            MonthName,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit

        FROM analytics.vw_SalesDetail

        GROUP BY
            MonthNumber,
            MonthName

        ORDER BY
            MonthNumber
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        return _read_dataframe(
            connection,
            query,
        )


def get_event_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_SALES",
    )

    query = """
        SELECT
            EventName,

            COUNT(
                DISTINCT FullDate
            ) AS Days,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

            SUM(Revenue)
                AS Revenue,

            SUM(GrossProfit)
                AS GrossProfit,

            SUM(Revenue)
            /
            NULLIF(
                COUNT(
                    DISTINCT FullDate
                ),
                0
            ) AS AvgDailyRevenue

        FROM
        (
            SELECT
                FullDate,
                OrderId,
                Revenue,
                GrossProfit,

                CASE
                    WHEN IsRamadan = 1
                        THEN 'Ramadan'

                    WHEN IsEidAlFitr = 1
                        THEN 'Eid Al Fitr'

                    WHEN IsEidAlAdha = 1
                        THEN 'Eid Al Adha'

                    WHEN IsWhiteFriday = 1
                        THEN 'White Friday'

                    WHEN IsEidAlEtihad = 1
                        THEN 'Eid Al Etihad'

                    WHEN IsSummer = 1
                        THEN 'Summer'

                    WHEN IsYearEndSeason = 1
                        THEN 'Year End'

                    ELSE 'Regular Days'
                END AS EventName

            FROM analytics.vw_SalesDetail
        ) x

        GROUP BY
            EventName

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
        )


def get_store_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_STORES",
    )

    query = """
        SELECT
            StoreId,
            StoreCode,
            StoreName,
            EmirateId,
            EmirateName,
            Orders,
            Customers,
            NetUnits,
            Revenue,
            GrossProfit,
            GrossMarginPct,
            AOV,
            GrossUnits,
            ReturnedUnits,
            ReturnRatePct

        FROM analytics.vw_StorePerformance

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
        )

    if not df.empty:
        total = df["Revenue"].sum()

        df[
            "RevenueSharePct"
        ] = (
            df["Revenue"]
            / total
            * 100
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


def get_category_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_PRODUCTS",
    )

    query = """
        SELECT
            CategoryId,
            CategoryName,

            COUNT(
                DISTINCT ProductId
            ) AS Products,

            COUNT(
                DISTINCT OrderId
            ) AS Orders,

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
                WHEN SUM(GrossUnits) = 0
                    THEN 0
                ELSE
                    SUM(ReturnedUnits)
                    * 100.0
                    / SUM(GrossUnits)
            END AS ReturnRatePct

        FROM analytics.vw_SalesDetail

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
        return _read_dataframe(
            connection,
            query,
        )


def get_brand_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_PRODUCTS",
    )

    query = """
        SELECT
            BrandId,
            BrandName,

            COUNT(
                DISTINCT ProductId
            ) AS Products,

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

        GROUP BY
            BrandId,
            BrandName

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
        )


def get_product_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_PRODUCTS",
    )

    query = """
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
            Orders,
            GrossUnits,
            ReturnedUnits,
            NetUnits,
            GrossSales,
            DiscountAmount,
            Revenue,
            NetCOGS,
            GrossProfit,
            GrossMarginPct,
            ReturnRatePct,
            DiscountDependencyPct

        FROM analytics.vw_ProductPerformance

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
        )


def get_product_pareto(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    df = get_product_performance(
        user,
        engine,
    )

    if df.empty:
        return df

    df = (
        df.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
        .copy()
    )

    total = float(
        df["Revenue"].sum()
    )

    if total:
        df[
            "RevenueSharePct"
        ] = (
            df["Revenue"]
            / total
            * 100
        )

        df[
            "CumulativeRevenuePct"
        ] = (
            df["Revenue"]
            .cumsum()
            / total
            * 100
        )
    else:
        df[
            "RevenueSharePct"
        ] = 0.0

        df[
            "CumulativeRevenuePct"
        ] = 0.0

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


def get_customer_rfm(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_any_permission(
        user,
        {
            "VIEW_RFM",
            "VIEW_CUSTOMERS",
        },
    )

    query = """
        WITH CustomerMetrics AS
        (
            SELECT
                CustomerId,

                MIN(FullDate)
                    AS FirstPurchaseDate,

                MAX(FullDate)
                    AS LastPurchaseDate,

                COUNT(
                    DISTINCT OrderId
                ) AS Frequency,

                SUM(NetUnits)
                    AS NetUnits,

                SUM(Revenue)
                    AS Monetary,

                SUM(GrossProfit)
                    AS GrossProfit

            FROM analytics.vw_SalesDetail

            GROUP BY
                CustomerId
        ),

        ReferenceDate AS
        (
            SELECT
                MAX(FullDate)
                    AS MaxDate
            FROM analytics.vw_SalesDetail
        )

        SELECT
            c.CustomerId,
            c.FirstPurchaseDate,
            c.LastPurchaseDate,

            DATEDIFF(
                DAY,
                c.LastPurchaseDate,
                r.MaxDate
            ) AS Recency,

            c.Frequency,
            c.NetUnits,
            c.Monetary,
            c.GrossProfit

        FROM CustomerMetrics c

        CROSS JOIN ReferenceDate r
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        df = _read_dataframe(
            connection,
            query,
        )

    if df.empty:
        return df

    df[
        "FirstPurchaseDate"
    ] = pd.to_datetime(
        df["FirstPurchaseDate"]
    )

    df[
        "LastPurchaseDate"
    ] = pd.to_datetime(
        df["LastPurchaseDate"]
    )

    df[
        "RScore"
    ] = pd.qcut(
        df["Recency"].rank(
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

    df[
        "FScore"
    ] = pd.qcut(
        df["Frequency"].rank(
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

    df[
        "MScore"
    ] = pd.qcut(
        df["Monetary"].rank(
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

    df[
        "RFMScore"
    ] = (
        df["RScore"]
        .astype(str)
        + df["FScore"]
        .astype(str)
        + df["MScore"]
        .astype(str)
    )

    def segment(row) -> str:
        recency = row["RScore"]
        frequency = row["FScore"]

        if (
            recency >= 4
            and frequency >= 4
        ):
            return "Champions"

        if (
            recency >= 3
            and frequency >= 4
        ):
            return "Loyal"

        if (
            recency >= 4
            and frequency <= 2
        ):
            return "Promising"

        if (
            recency <= 2
            and frequency >= 4
        ):
            return "At Risk"

        if (
            recency <= 2
            and frequency <= 2
        ):
            return "Hibernating"

        return "Potential Loyalists"

    df["Segment"] = (
        df.apply(
            segment,
            axis=1,
        )
    )

    return df


def get_customer_concentration(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    df = get_customer_rfm(
        user,
        engine,
    )

    if df.empty:
        return df

    result = (
        df.sort_values(
            "Monetary",
            ascending=False,
        )
        .reset_index(drop=True)
        .copy()
    )

    total = float(
        result["Monetary"].sum()
    )

    result[
        "CustomerRank"
    ] = (
        result.index + 1
    )

    result[
        "CustomerPct"
    ] = (
        result[
            "CustomerRank"
        ]
        / len(result)
        * 100
    )

    result[
        "CumulativeRevenuePct"
    ] = (
        result["Monetary"]
        .cumsum()
        / total
        * 100
        if total
        else 0
    )

    return result


def get_cohort_retention(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_any_permission(
        user,
        {
            "VIEW_COHORTS",
            "VIEW_CUSTOMERS",
        },
    )

    query = """
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
                        WHEN CohortIndex = 0
                        THEN ActiveCustomers
                    END
                ) OVER
                (
                    PARTITION BY CohortMonth
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
        )

    if not df.empty:
        df["CohortMonth"] = (
            pd.to_datetime(
                df["CohortMonth"]
            )
        )

        df["PurchaseMonth"] = (
            pd.to_datetime(
                df["PurchaseMonth"]
            )
        )

    return df


def get_returns(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_RETURNS",
    )

    query = """
        SELECT *
        FROM analytics.vw_ReturnAnalysis
        ORDER BY
            ReturnDateTime DESC
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        dataframe = _read_dataframe(
            connection,
            query,
        )

    for column in [
        "ReturnDateTime",
        "ReturnDate",
        "OrderDateTime",
        "OrderDate",
    ]:
        if column in dataframe.columns:
            dataframe[
                column
            ] = pd.to_datetime(
                dataframe[column]
            )

    return dataframe


def get_return_summary(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_RETURNS",
    )

    query = """
        SELECT
            ReturnReason,

            COUNT_BIG(*)
                AS ReturnLines,

            SUM(ReturnQuantity)
                AS ReturnedUnits,

            SUM(ReturnedNetAmount)
                AS ReturnedNetAmount,

            SUM(RefundAmount)
                AS RefundAmount,

            AVG(
                CAST(
                    ReturnLagDays
                    AS FLOAT
                )
            ) AS AvgReturnLagDays

        FROM analytics.vw_ReturnAnalysis

        GROUP BY
            ReturnReason

        ORDER BY
            ReturnedUnits DESC
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        return _read_dataframe(
            connection,
            query,
        )


def get_inventory_status(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_INVENTORY",
    )

    query = """
        SELECT *
        FROM analytics.vw_InventoryStatus
        ORDER BY
            StoreCode,
            SKU
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        dataframe = _read_dataframe(
            connection,
            query,
        )

    if (
        "LastSaleDate"
        in dataframe.columns
    ):
        dataframe[
            "LastSaleDate"
        ] = pd.to_datetime(
            dataframe[
                "LastSaleDate"
            ]
        )

    return dataframe


def get_target_performance(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_TARGETS",
    )

    query = """
        SELECT *
        FROM analytics.vw_TargetPerformance
        ORDER BY
            MonthStart,
            StoreCode
    """

    with user_database_connection(
        user_id=user.user_id,
        engine=engine,
    ) as connection:
        dataframe = _read_dataframe(
            connection,
            query,
        )

    if (
        "MonthStart"
        in dataframe.columns
    ):
        dataframe[
            "MonthStart"
        ] = pd.to_datetime(
            dataframe[
                "MonthStart"
            ]
        )

    return dataframe


def get_monthly_targets(
    user: AuthenticatedUser,
    engine: Engine | None = None,
) -> pd.DataFrame:
    _require_permission(
        user,
        "VIEW_TARGETS",
    )

    query = """
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
        )

    if not df.empty:
        df[
            "MonthStart"
        ] = pd.to_datetime(
            df["MonthStart"]
        )

        df[
            "RevenueAchievementPct"
        ] = np.where(
            df["RevenueTarget"] != 0,
            df["ActualRevenue"]
            * 100.0
            / df["RevenueTarget"],
            np.nan,
        )

        df[
            "RevenueVariance"
        ] = (
            df["ActualRevenue"]
            - df["RevenueTarget"]
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
            "OrdersAchievementPct"
        ] = np.where(
            df["OrdersTarget"] != 0,
            df["ActualOrders"]
            * 100.0
            / df["OrdersTarget"],
            np.nan,
        )

    return df