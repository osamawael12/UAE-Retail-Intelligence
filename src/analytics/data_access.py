"""
UAE Retail Intelligence Platform
Analytics Data Access Layer

Reusable SQL Server access functions for:
- Python EDA
- Statistical analysis
- Forecasting preparation

The module reads from the validated analytics schema.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.database.connection import get_engine


ANALYTICS_VIEWS = {
    "sales_detail": "analytics.vw_SalesDetail",
    "daily_sales": "analytics.vw_DailySales",
    "store_performance": "analytics.vw_StorePerformance",
    "product_performance": "analytics.vw_ProductPerformance",
    "customer_360": "analytics.vw_Customer360",
    "return_analysis": "analytics.vw_ReturnAnalysis",
    "inventory_status": "analytics.vw_InventoryStatus",
    "target_performance": "analytics.vw_TargetPerformance",
}


def _get_engine(
    engine: Engine | None = None,
) -> Engine:
    if engine is not None:
        return engine

    return get_engine()


def _validate_date_range(
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
            "start_date cannot be after end_date."
        )

    return start, end


def read_view(
    view_name: str,
    engine: Engine | None = None,
) -> pd.DataFrame:
    if view_name not in ANALYTICS_VIEWS:
        raise ValueError(
            f"Unsupported analytics view: "
            f"{view_name}"
        )

    view = ANALYTICS_VIEWS[
        view_name
    ]

    query = text(
        f"""
        SELECT *
        FROM {view}
        """
    )

    return pd.read_sql_query(
        query,
        _get_engine(engine),
    )


def get_dataset_overview(
    engine: Engine | None = None,
) -> pd.DataFrame:
    """
    Row counts for all analytics views.

    RecordCount is intentionally used instead of RowCount,
    because ROWCOUNT has special meaning in T-SQL.
    """

    query = text(
        """
        SELECT
            'Sales Detail' AS Dataset,
            COUNT_BIG(*) AS RecordCount
        FROM analytics.vw_SalesDetail

        UNION ALL

        SELECT
            'Daily Sales',
            COUNT_BIG(*)
        FROM analytics.vw_DailySales

        UNION ALL

        SELECT
            'Stores',
            COUNT_BIG(*)
        FROM analytics.vw_StorePerformance

        UNION ALL

        SELECT
            'Products',
            COUNT_BIG(*)
        FROM analytics.vw_ProductPerformance

        UNION ALL

        SELECT
            'Customers',
            COUNT_BIG(*)
        FROM analytics.vw_Customer360

        UNION ALL

        SELECT
            'Returns',
            COUNT_BIG(*)
        FROM analytics.vw_ReturnAnalysis

        UNION ALL

        SELECT
            'Inventory',
            COUNT_BIG(*)
        FROM analytics.vw_InventoryStatus

        UNION ALL

        SELECT
            'Targets',
            COUNT_BIG(*)
        FROM analytics.vw_TargetPerformance
        """
    )

    return pd.read_sql_query(
        query,
        _get_engine(engine),
    )


def get_executive_summary(
    engine: Engine | None = None,
) -> dict:
    query = text(
        """
        SELECT
            SUM(Revenue) AS Revenue,

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
        """
    )

    dataframe = pd.read_sql_query(
        query,
        _get_engine(engine),
    )

    if dataframe.empty:
        raise RuntimeError(
            "Executive summary returned "
            "no data."
        )

    return (
        dataframe.iloc[0]
        .to_dict()
    )


def get_company_daily_sales(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    start, end = (
        _validate_date_range(
            start_date,
            end_date,
        )
    )

    conditions = [
        "1 = 1"
    ]

    parameters = {}

    if start is not None:
        conditions.append(
            "FullDate >= :start_date"
        )
        parameters[
            "start_date"
        ] = start.date()

    if end is not None:
        conditions.append(
            "FullDate <= :end_date"
        )
        parameters[
            "end_date"
        ] = end.date()

    where_clause = (
        " AND ".join(
            conditions
        )
    )

    query = text(
        f"""
        SELECT
            FullDate,

            SUM(Orders)
                AS Orders,

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

            SUM(NetSalesBeforeReturns)
                AS NetSalesBeforeReturns,

            SUM(ReturnedNetSales)
                AS ReturnedNetSales,

            SUM(Revenue)
                AS Revenue,

            SUM(NetCOGS)
                AS NetCOGS,

            SUM(GrossProfit)
                AS GrossProfit,

            SUM(VATCollected)
                AS VATCollected

        FROM analytics.vw_DailySales

        WHERE
            {where_clause}

        GROUP BY
            FullDate

        ORDER BY
            FullDate
        """
    )

    dataframe = pd.read_sql_query(
        query,
        _get_engine(engine),
        params=parameters,
    )

    dataframe[
        "FullDate"
    ] = pd.to_datetime(
        dataframe[
            "FullDate"
        ]
    )

    return dataframe


def get_monthly_company_sales(
    engine: Engine | None = None,
) -> pd.DataFrame:
    query = text(
        """
        SELECT
            DATEFROMPARTS(
                YearNumber,
                MonthNumber,
                1
            ) AS MonthStart,

            SUM(Orders)
                AS Orders,

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

            SUM(NetSalesBeforeReturns)
                AS NetSalesBeforeReturns,

            SUM(ReturnedNetSales)
                AS ReturnedNetSales,

            SUM(Revenue)
                AS Revenue,

            SUM(NetCOGS)
                AS NetCOGS,

            SUM(GrossProfit)
                AS GrossProfit,

            SUM(VATCollected)
                AS VATCollected

        FROM analytics.vw_DailySales

        GROUP BY
            YearNumber,
            MonthNumber

        ORDER BY
            MonthStart
        """
    )

    dataframe = pd.read_sql_query(
        query,
        _get_engine(engine),
    )

    dataframe[
        "MonthStart"
    ] = pd.to_datetime(
        dataframe[
            "MonthStart"
        ]
    )

    return dataframe


def get_sales_detail(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    store_id: int | None = None,
    emirate_id: int | None = None,
    category_id: int | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    start, end = (
        _validate_date_range(
            start_date,
            end_date,
        )
    )

    conditions = [
        "1 = 1"
    ]

    parameters = {}

    if start is not None:
        conditions.append(
            "FullDate >= :start_date"
        )
        parameters[
            "start_date"
        ] = start.date()

    if end is not None:
        conditions.append(
            "FullDate <= :end_date"
        )
        parameters[
            "end_date"
        ] = end.date()

    if store_id is not None:
        conditions.append(
            "StoreId = :store_id"
        )
        parameters[
            "store_id"
        ] = int(store_id)

    if emirate_id is not None:
        conditions.append(
            "EmirateId = :emirate_id"
        )
        parameters[
            "emirate_id"
        ] = int(emirate_id)

    if category_id is not None:
        conditions.append(
            "CategoryId = :category_id"
        )
        parameters[
            "category_id"
        ] = int(category_id)

    query = text(
        f"""
        SELECT *
        FROM analytics.vw_SalesDetail
        WHERE
            {' AND '.join(conditions)}
        ORDER BY
            OrderDateTime,
            OrderItemId
        """
    )

    dataframe = pd.read_sql_query(
        query,
        _get_engine(engine),
        params=parameters,
    )

    for column in [
        "FullDate",
        "OrderDateTime",
    ]:
        if column in dataframe.columns:
            dataframe[
                column
            ] = pd.to_datetime(
                dataframe[
                    column
                ]
            )

    return dataframe


def get_store_performance(
    engine: Engine | None = None,
) -> pd.DataFrame:
    return read_view(
        "store_performance",
        engine,
    )


def get_product_performance(
    engine: Engine | None = None,
) -> pd.DataFrame:
    return read_view(
        "product_performance",
        engine,
    )


def get_customer_360(
    engine: Engine | None = None,
) -> pd.DataFrame:
    dataframe = read_view(
        "customer_360",
        engine,
    )

    for column in [
        "RegistrationDate",
        "FirstPurchaseDate",
        "LastPurchaseDate",
    ]:
        if column in dataframe.columns:
            dataframe[
                column
            ] = pd.to_datetime(
                dataframe[
                    column
                ]
            )

    return dataframe


def get_returns(
    engine: Engine | None = None,
) -> pd.DataFrame:
    dataframe = read_view(
        "return_analysis",
        engine,
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
                dataframe[
                    column
                ]
            )

    return dataframe


def get_inventory_status(
    engine: Engine | None = None,
) -> pd.DataFrame:
    dataframe = read_view(
        "inventory_status",
        engine,
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
    engine: Engine | None = None,
) -> pd.DataFrame:
    dataframe = read_view(
        "target_performance",
        engine,
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