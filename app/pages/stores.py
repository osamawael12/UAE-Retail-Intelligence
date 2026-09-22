from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components import (
    dataframe_config,
    insight_card,
    metric,
    money,
    number,
    page_header,
    percentage,
    section_header,
    secure_csv_download,
    style_figure,
)
from app.theme import (
    COLORS,
    EMIRATE_COLORS,
)
from src.analytics.filtered_data import (
    get_filtered_emirate_performance,
    get_filtered_store_performance,
)


# ============================================================
# Helpers
# ============================================================

def _safe_float(
    value,
    default: float = 0.0,
) -> float:
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass

    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if not math.isfinite(
        result
    ):
        return default

    return result


def _period_label(
    filters,
) -> str:
    if (
        filters.start_date
        is not None
        and filters.end_date
        is not None
    ):
        return (
            f"{filters.start_date:%d %b %Y}"
            " - "
            f"{filters.end_date:%d %b %Y}"
        )

    return "Full available history"


def _zscore(
    series: pd.Series,
) -> pd.Series:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    standard_deviation = (
        numeric.std(
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
                len(numeric)
            ),
            index=numeric.index,
        )

    return (
        numeric
        - numeric.mean()
    ) / standard_deviation


def _min_max_score(
    series: pd.Series,
    reverse: bool = False,
) -> pd.Series:
    numeric = (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .fillna(0)
    )

    minimum = float(
        numeric.min()
    )

    maximum = float(
        numeric.max()
    )

    if maximum == minimum:
        score = pd.Series(
            np.full(
                len(numeric),
                50.0,
            ),
            index=numeric.index,
        )

    else:
        score = (
            (
                numeric
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


# ============================================================
# Data Preparation
# ============================================================

def _prepare_stores(
    stores: pd.DataFrame,
) -> pd.DataFrame:
    data = stores.copy()

    if data.empty:
        return data

    total_revenue = _safe_float(
        data[
            "Revenue"
        ].sum()
    )

    total_profit = _safe_float(
        data[
            "GrossProfit"
        ].sum()
    )

    total_orders = _safe_float(
        data[
            "Orders"
        ].sum()
    )

    total_customers = _safe_float(
        data[
            "Customers"
        ].sum()
    )

    if (
        "RevenueSharePct"
        not in data.columns
    ):
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
        "ProfitSharePct"
    ] = (
        data[
            "GrossProfit"
        ]
        / total_profit
        * 100
        if total_profit
        else 0
    )

    data[
        "OrderSharePct"
    ] = (
        data[
            "Orders"
        ]
        / total_orders
        * 100
        if total_orders
        else 0
    )

    data[
        "CustomerSharePct"
    ] = (
        data[
            "Customers"
        ]
        / total_customers
        * 100
        if total_customers
        else 0
    )

    data[
        "OrdersPerCustomer"
    ] = np.where(
        data[
            "Customers"
        ] != 0,
        data[
            "Orders"
        ]
        / data[
            "Customers"
        ],
        0,
    )

    data[
        "RevenuePerCustomer"
    ] = np.where(
        data[
            "Customers"
        ] != 0,
        data[
            "Revenue"
        ]
        / data[
            "Customers"
        ],
        0,
    )

    data[
        "ProfitPerOrder"
    ] = np.where(
        data[
            "Orders"
        ] != 0,
        data[
            "GrossProfit"
        ]
        / data[
            "Orders"
        ],
        0,
    )

    data[
        "NetUnitsPerOrder"
    ] = np.where(
        data[
            "Orders"
        ] != 0,
        data[
            "NetUnits"
        ]
        / data[
            "Orders"
        ],
        0,
    )

    median_revenue = (
        data[
            "Revenue"
        ].median()
    )

    median_margin = (
        data[
            "GrossMarginPct"
        ].median()
    )

    data[
        "PerformanceQuadrant"
    ] = np.select(
        [
            (
                data[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),

            (
                data[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                < median_margin
            ),

            (
                data[
                    "Revenue"
                ]
                < median_revenue
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),
        ],
        [
            "Leaders",
            "Scale / Margin Pressure",
            "Efficient / Lower Scale",
        ],
        default=(
            "Performance Watch"
        ),
    )

    revenue_score = (
        _min_max_score(
            data[
                "Revenue"
            ]
        )
    )

    profit_score = (
        _min_max_score(
            data[
                "GrossProfit"
            ]
        )
    )

    margin_score = (
        _min_max_score(
            data[
                "GrossMarginPct"
            ]
        )
    )

    aov_score = (
        _min_max_score(
            data["AOV"]
        )
    )

    return_health_score = (
        _min_max_score(
            data[
                "ReturnRatePct"
            ],
            reverse=True,
        )
    )

    data[
        "PerformanceScore"
    ] = (
        revenue_score
        * 0.30
        + profit_score
        * 0.25
        + margin_score
        * 0.20
        + aov_score
        * 0.10
        + return_health_score
        * 0.15
    )

    data[
        "PerformanceScore"
    ] = (
        data[
            "PerformanceScore"
        ]
        .clip(
            0,
            100,
        )
    )

    data[
        "PerformanceTier"
    ] = pd.cut(
        data[
            "PerformanceScore"
        ],
        bins=[
            -np.inf,
            40,
            60,
            80,
            np.inf,
        ],
        labels=[
            "Priority Review",
            "Developing",
            "Strong",
            "Leading",
        ],
    )

    data[
        "RevenueZScore"
    ] = _zscore(
        data[
            "Revenue"
        ]
    )

    data[
        "MarginZScore"
    ] = _zscore(
        data[
            "GrossMarginPct"
        ]
    )

    data[
        "ReturnZScore"
    ] = _zscore(
        data[
            "ReturnRatePct"
        ]
    )

    data[
        "IsRevenueOutlier"
    ] = (
        data[
            "RevenueZScore"
        ]
        .abs()
        >= 2
    )

    data[
        "IsMarginOutlier"
    ] = (
        data[
            "MarginZScore"
        ]
        .abs()
        >= 2
    )

    data[
        "IsReturnRiskOutlier"
    ] = (
        data[
            "ReturnZScore"
        ]
        >= 2
    )

    data[
        "AttentionFlag"
    ] = np.select(
        [
            (
                data[
                    "ReturnRatePct"
                ]
                >= data[
                    "ReturnRatePct"
                ].quantile(
                    .75
                )
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                <= data[
                    "GrossMarginPct"
                ].quantile(
                    .25
                )
            ),

            (
                data[
                    "Revenue"
                ]
                >= data[
                    "Revenue"
                ].median()
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                <= data[
                    "GrossMarginPct"
                ].quantile(
                    .25
                )
            ),

            (
                data[
                    "Revenue"
                ]
                <= data[
                    "Revenue"
                ].quantile(
                    .25
                )
            )
            & (
                data[
                    "ReturnRatePct"
                ]
                >= data[
                    "ReturnRatePct"
                ].quantile(
                    .75
                )
            ),
        ],
        [
            "Margin + Return Risk",
            "High Scale / Margin Pressure",
            "Low Scale / Return Risk",
        ],
        default="Normal",
    )

    return data


def _prepare_emirates(
    emirates: pd.DataFrame,
    stores: pd.DataFrame,
) -> pd.DataFrame:
    data = emirates.copy()

    if data.empty:
        return data

    total_revenue = _safe_float(
        data[
            "Revenue"
        ].sum()
    )

    total_profit = _safe_float(
        data[
            "GrossProfit"
        ].sum()
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
        "ProfitSharePct"
    ] = (
        data[
            "GrossProfit"
        ]
        / total_profit
        * 100
        if total_profit
        else 0
    )

    data[
        "RevenuePerStore"
    ] = np.where(
        data[
            "Stores"
        ] != 0,
        data[
            "Revenue"
        ]
        / data[
            "Stores"
        ],
        0,
    )

    data[
        "OrdersPerStore"
    ] = np.where(
        data[
            "Stores"
        ] != 0,
        data[
            "Orders"
        ]
        / data[
            "Stores"
        ],
        0,
    )

    data[
        "CustomersPerStore"
    ] = np.where(
        data[
            "Stores"
        ] != 0,
        data[
            "Customers"
        ]
        / data[
            "Stores"
        ],
        0,
    )

    data[
        "RevenuePerCustomer"
    ] = np.where(
        data[
            "Customers"
        ] != 0,
        data[
            "Revenue"
        ]
        / data[
            "Customers"
        ],
        0,
    )

    if not stores.empty:
        dispersion = (
            stores.groupby(
                "EmirateName",
                as_index=False,
            )
            .agg(
                StoreRevenueStd=(
                    "Revenue",
                    "std",
                ),
                StoreRevenueMean=(
                    "Revenue",
                    "mean",
                ),
                BestStoreRevenue=(
                    "Revenue",
                    "max",
                ),
                LowestStoreRevenue=(
                    "Revenue",
                    "min",
                ),
            )
        )

        dispersion[
            "StoreRevenueCVPct"
        ] = np.where(
            dispersion[
                "StoreRevenueMean"
            ] != 0,
            dispersion[
                "StoreRevenueStd"
            ]
            / dispersion[
                "StoreRevenueMean"
            ]
            * 100,
            0,
        )

        data = data.merge(
            dispersion,
            on="EmirateName",
            how="left",
        )

    return data


# ============================================================
# KPI Section
# ============================================================

def _render_network_kpis(
    stores: pd.DataFrame,
    emirates: pd.DataFrame,
) -> None:
    section_header(
        "UAE Network KPI Pulse",
        (
            "Store network scale, commercial "
            "contribution and operational quality."
        ),
    )

    revenue = _safe_float(
        stores[
            "Revenue"
        ].sum()
    )

    profit = _safe_float(
        stores[
            "GrossProfit"
        ].sum()
    )

    orders = _safe_float(
        stores[
            "Orders"
        ].sum()
    )

    customers = _safe_float(
        stores[
            "Customers"
        ].sum()
    )

    margin = (
        profit
        / revenue
        * 100
        if revenue
        else 0
    )

    weighted_return_rate = (
        (
            stores[
                "ReturnedUnits"
            ].sum()
            * 100
            / stores[
                "GrossUnits"
            ].sum()
        )
        if (
            stores[
                "GrossUnits"
            ].sum()
            != 0
        )
        else 0
    )

    row = st.columns(4)

    metric(
        row[0],
        "Visible Stores",
        number(
            len(stores)
        ),
    )

    metric(
        row[1],
        "Visible Emirates",
        number(
            len(emirates)
        ),
    )

    metric(
        row[2],
        "Network Revenue",
        money(revenue),
    )

    metric(
        row[3],
        "Gross Profit",
        money(profit),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Network Margin",
        percentage(margin),
    )

    metric(
        row[1],
        "Orders",
        number(orders),
    )

    metric(
        row[2],
        "Customers",
        number(customers),
    )

    metric(
        row[3],
        "Weighted Return Rate",
        percentage(
            weighted_return_rate
        ),
    )


# ============================================================
# Network Signals
# ============================================================

def _render_network_signals(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Management Signals",
        (
            "High-level network indicators for "
            "store portfolio review."
        ),
    )

    top_store = (
        stores.sort_values(
            "Revenue",
            ascending=False,
        )
        .iloc[0]
    )

    best_margin_store = (
        stores.sort_values(
            "GrossMarginPct",
            ascending=False,
        )
        .iloc[0]
    )

    highest_return_store = (
        stores.sort_values(
            "ReturnRatePct",
            ascending=False,
        )
        .iloc[0]
    )

    total_revenue = _safe_float(
        stores[
            "Revenue"
        ].sum()
    )

    top5_share = (
        _safe_float(
            stores.nlargest(
                min(
                    5,
                    len(stores),
                ),
                "Revenue",
            )[
                "Revenue"
            ].sum()
        )
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "TOP REVENUE STORE",
            str(
                top_store[
                    "StoreCode"
                ]
            ),
            money(
                top_store[
                    "Revenue"
                ]
            ),
            "green",
        )

    with columns[1]:
        insight_card(
            "BEST MARGIN STORE",
            str(
                best_margin_store[
                    "StoreCode"
                ]
            ),
            percentage(
                best_margin_store[
                    "GrossMarginPct"
                ]
            ),
            "green",
        )

    with columns[2]:
        insight_card(
            "HIGHEST RETURN RATE",
            str(
                highest_return_store[
                    "StoreCode"
                ]
            ),
            percentage(
                highest_return_store[
                    "ReturnRatePct"
                ]
            ),
            "red",
        )

    with columns[3]:
        insight_card(
            "TOP 5 REVENUE SHARE",
            percentage(
                top5_share
            ),
            (
                "Network revenue concentration "
                "in the top five visible stores."
            ),
            (
                "red"
                if top5_share >= 60
                else "gold"
                if top5_share >= 40
                else "green"
            ),
        )


# ============================================================
# Emirate Analysis
# ============================================================

def _render_emirate_analysis(
    emirates: pd.DataFrame,
) -> None:
    section_header(
        "Emirate Performance",
        (
            "Revenue contribution, productivity, "
            "margin and customer economics by emirate."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            emirates.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            text="RevenueSharePct",
            hover_data=[
                "Stores",
                "Orders",
                "Customers",
                "GrossMarginPct",
            ],
            title=(
                "Revenue Contribution by Emirate"
            ),
        )

        figure.update_traces(
            texttemplate=(
                "%{text:.1f}%"
            ),
            textposition="outside",
        )

        figure.update_layout(
            showlegend=False,
            xaxis_title="Revenue",
            yaxis_title=None,
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
                legend=False,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            emirates,
            x="RevenuePerStore",
            y="GrossMarginPct",
            size="Revenue",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_name=(
                "EmirateName"
            ),
            hover_data=[
                "Stores",
                "RevenueSharePct",
                "OrdersPerStore",
                "CustomersPerStore",
                "RevenuePerCustomer",
            ],
            title=(
                "Emirate Productivity / Margin"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
            ),
            use_container_width=True,
        )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            emirates.sort_values(
                "RevenuePerStore"
            ),
            x="RevenuePerStore",
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            title=(
                "Revenue Productivity per Store"
            ),
        )

        figure.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
                legend=False,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            emirates.sort_values(
                "RevenuePerCustomer"
            ),
            x="RevenuePerCustomer",
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            title=(
                "Revenue per Customer by Emirate"
            ),
        )

        figure.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
                legend=False,
            ),
            use_container_width=True,
        )


# ============================================================
# Store Ranking
# ============================================================

def _render_store_ranking(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Store Ranking",
        (
            "Top and bottom performance across "
            "revenue, profit and margin."
        ),
    )

    count = min(
        12,
        len(stores),
    )

    left, right = st.columns(2)

    with left:
        top = (
            stores.nlargest(
                count,
                "Revenue",
            )
            .sort_values(
                "Revenue"
            )
        )

        figure = px.bar(
            top,
            x="Revenue",
            y="StoreCode",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "StoreName",
                "GrossProfit",
                "GrossMarginPct",
                "RevenueSharePct",
            ],
            title=(
                "Top Stores by Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                500,
            ),
            use_container_width=True,
        )

    with right:
        bottom = (
            stores.nsmallest(
                count,
                "Revenue",
            )
            .sort_values(
                "Revenue",
                ascending=False,
            )
        )

        figure = px.bar(
            bottom,
            x="Revenue",
            y="StoreCode",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "StoreName",
                "EmirateName",
                "ReturnRatePct",
            ],
            title=(
                "Lowest Revenue Stores"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                500,
            ),
            use_container_width=True,
        )

    left, right = st.columns(2)

    with left:
        profit = (
            stores.nlargest(
                count,
                "GrossProfit",
            )
            .sort_values(
                "GrossProfit"
            )
        )

        figure = px.bar(
            profit,
            x="GrossProfit",
            y="StoreCode",
            orientation="h",
            color="GrossMarginPct",
            title=(
                "Top Stores by Gross Profit"
            ),
            color_continuous_scale=(
                "YlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                480,
            ),
            use_container_width=True,
        )

    with right:
        margin = (
            stores.nlargest(
                count,
                "GrossMarginPct",
            )
            .sort_values(
                "GrossMarginPct"
            )
        )

        figure = px.bar(
            margin,
            x="GrossMarginPct",
            y="StoreCode",
            orientation="h",
            color="Revenue",
            title=(
                "Highest Margin Stores"
            ),
            color_continuous_scale=(
                "Viridis"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                480,
            ),
            use_container_width=True,
        )


# ============================================================
# Quadrant Analysis
# ============================================================

def _render_quadrants(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Revenue / Margin Quadrants",
        (
            "Portfolio segmentation around the "
            "visible network median revenue and margin."
        ),
    )

    median_revenue = _safe_float(
        stores[
            "Revenue"
        ].median()
    )

    median_margin = _safe_float(
        stores[
            "GrossMarginPct"
        ].median()
    )

    figure = px.scatter(
        stores,
        x="Revenue",
        y="GrossMarginPct",
        size="Orders",
        color="PerformanceQuadrant",
        hover_name="StoreName",
        hover_data=[
            "StoreCode",
            "EmirateName",
            "Customers",
            "AOV",
            "ReturnRatePct",
            "PerformanceScore",
        ],
        title=(
            "Store Portfolio Quadrant Matrix"
        ),
        color_discrete_map={
            "Leaders":
                COLORS[
                    "uae_green"
                ],

            "Scale / Margin Pressure":
                COLORS["gold"],

            "Efficient / Lower Scale":
                COLORS["info"],

            "Performance Watch":
                COLORS[
                    "uae_red"
                ],
        },
    )

    figure.add_vline(
        x=median_revenue,
        line_dash="dash",
        line_color=(
            COLORS["muted"]
        ),
    )

    figure.add_hline(
        y=median_margin,
        line_dash="dash",
        line_color=(
            COLORS["muted"]
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            520,
        ),
        use_container_width=True,
    )

    quadrant = (
        stores.groupby(
            "PerformanceQuadrant",
            as_index=False,
        )
        .agg(
            Stores=(
                "StoreId",
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
        )
    )

    quadrant[
        "RevenueSharePct"
    ] = (
        quadrant[
            "Revenue"
        ]
        / quadrant[
            "Revenue"
        ].sum()
        * 100
        if quadrant[
            "Revenue"
        ].sum()
        else 0
    )

    figure = px.bar(
        quadrant,
        x="PerformanceQuadrant",
        y="Revenue",
        color="PerformanceQuadrant",
        text="Stores",
        title=(
            "Revenue by Performance Quadrant"
        ),
        color_discrete_map={
            "Leaders":
                COLORS[
                    "uae_green"
                ],

            "Scale / Margin Pressure":
                COLORS["gold"],

            "Efficient / Lower Scale":
                COLORS["info"],

            "Performance Watch":
                COLORS[
                    "uae_red"
                ],
        },
    )

    figure.update_layout(
        showlegend=False,
        xaxis_title=None,
    )

    st.plotly_chart(
        style_figure(
            figure,
            410,
            legend=False,
        ),
        use_container_width=True,
    )


# ============================================================
# Performance Score
# ============================================================

def _render_performance_score(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Composite Store Performance Score",
        (
            "Relative portfolio score combining revenue, "
            "profit, margin, AOV and return health. "
            "Designed for prioritization, not accounting."
        ),
    )

    ranked = (
        stores.sort_values(
            "PerformanceScore",
            ascending=False,
        )
        .copy()
    )

    figure = px.bar(
        ranked.sort_values(
            "PerformanceScore"
        ),
        x="PerformanceScore",
        y="StoreCode",
        orientation="h",
        color="PerformanceTier",
        hover_data=[
            "StoreName",
            "EmirateName",
            "Revenue",
            "GrossMarginPct",
            "ReturnRatePct",
        ],
        title=(
            "Relative Store Performance Score"
        ),
        color_discrete_map={
            "Leading":
                COLORS[
                    "uae_green"
                ],

            "Strong":
                COLORS["info"],

            "Developing":
                COLORS["gold"],

            "Priority Review":
                COLORS[
                    "uae_red"
                ],
        },
    )

    figure.update_layout(
        xaxis=dict(
            range=[
                0,
                100,
            ]
        )
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                520,
                len(stores)
                * 23,
            ),
        ),
        use_container_width=True,
    )

    st.caption(
        "Performance Score weights: Revenue 30%, "
        "Gross Profit 25%, Margin 20%, "
        "Return Health 15%, AOV 10%."
    )


# ============================================================
# Customer / Basket Economics
# ============================================================

def _render_customer_economics(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Customer & Basket Economics",
        (
            "Store-level relationships between "
            "customer scale, frequency, AOV and value."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.scatter(
            stores,
            x="Customers",
            y="RevenuePerCustomer",
            size="Revenue",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_name="StoreName",
            hover_data=[
                "StoreCode",
                "OrdersPerCustomer",
                "AOV",
            ],
            title=(
                "Customer Scale vs Value"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            stores,
            x="OrdersPerCustomer",
            y="AOV",
            size="Revenue",
            color="GrossMarginPct",
            hover_name="StoreName",
            hover_data=[
                "StoreCode",
                "EmirateName",
                "RevenuePerCustomer",
            ],
            title=(
                "Frequency vs Average Order Value"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    figure = px.scatter(
        stores,
        x="NetUnitsPerOrder",
        y="AOV",
        size="Orders",
        color="EmirateName",
        color_discrete_map=(
            EMIRATE_COLORS
        ),
        hover_name="StoreName",
        title=(
            "Basket Units vs Basket Value"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            420,
        ),
        use_container_width=True,
    )


# ============================================================
# Return Risk
# ============================================================

def _render_return_risk(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Return Risk & Margin Pressure",
        (
            "Store return exposure relative to "
            "commercial profitability."
        ),
    )

    left, right = st.columns(2)

    with left:
        risk = (
            stores.sort_values(
                "ReturnRatePct",
                ascending=False,
            )
            .head(
                min(
                    15,
                    len(stores),
                )
            )
            .sort_values(
                "ReturnRatePct"
            )
        )

        figure = px.bar(
            risk,
            x="ReturnRatePct",
            y="StoreCode",
            orientation="h",
            color="ReturnRatePct",
            hover_data=[
                "StoreName",
                "EmirateName",
                "Revenue",
                "GrossMarginPct",
            ],
            title=(
                "Highest Return Rate Stores"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        figure.update_layout(
            coloraxis_showscale=False,
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            stores,
            x="ReturnRatePct",
            y="GrossMarginPct",
            size="Revenue",
            color="AttentionFlag",
            hover_name="StoreName",
            hover_data=[
                "StoreCode",
                "EmirateName",
                "PerformanceScore",
            ],
            title=(
                "Return / Margin Risk Matrix"
            ),
            color_discrete_map={
                "Normal":
                    COLORS[
                        "uae_green"
                    ],

                "Margin + Return Risk":
                    COLORS[
                        "uae_red"
                    ],

                "High Scale / Margin Pressure":
                    COLORS["gold"],

                "Low Scale / Return Risk":
                    "#E88A32",
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )


# ============================================================
# Concentration
# ============================================================

def _render_concentration(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Revenue Concentration",
        (
            "Store contribution curve showing "
            "dependency on leading locations."
        ),
    )

    concentration = (
        stores.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
        .copy()
    )

    total = _safe_float(
        concentration[
            "Revenue"
        ].sum()
    )

    concentration[
        "StoreRank"
    ] = (
        concentration.index
        + 1
    )

    concentration[
        "StorePct"
    ] = (
        concentration[
            "StoreRank"
        ]
        / len(
            concentration
        )
        * 100
    )

    concentration[
        "CumulativeRevenuePct"
    ] = (
        concentration[
            "Revenue"
        ]
        .cumsum()
        / total
        * 100
        if total
        else 0
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=concentration[
                "StoreCode"
            ],
            y=concentration[
                "Revenue"
            ],
            name="Revenue",
            marker_color=(
                COLORS[
                    "uae_green"
                ]
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=concentration[
                "StoreCode"
            ],
            y=concentration[
                "CumulativeRevenuePct"
            ],
            name="Cumulative %",
            yaxis="y2",
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=3,
            ),
            mode="lines+markers",
        )
    )

    figure.update_layout(
        title=(
            "Store Revenue Pareto"
        ),
        yaxis_title="Revenue",
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[
                0,
                105,
            ],
            title=(
                "Cumulative Revenue %"
            ),
            gridcolor=(
                "rgba(0,0,0,0)"
            ),
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            480,
        ),
        use_container_width=True,
    )


# ============================================================
# Outliers
# ============================================================

def _render_outliers(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Store Outlier Screening",
        (
            "Statistical screening for unusual revenue, "
            "margin or return behavior. Flags are "
            "diagnostic candidates, not confirmed issues."
        ),
    )

    candidates = (
        stores[
            (
                stores[
                    "IsRevenueOutlier"
                ]
            )
            | (
                stores[
                    "IsMarginOutlier"
                ]
            )
            | (
                stores[
                    "IsReturnRiskOutlier"
                ]
            )
        ]
        .copy()
    )

    columns = st.columns(3)

    metric(
        columns[0],
        "Revenue Outliers",
        number(
            stores[
                "IsRevenueOutlier"
            ].sum()
        ),
    )

    metric(
        columns[1],
        "Margin Outliers",
        number(
            stores[
                "IsMarginOutlier"
            ].sum()
        ),
    )

    metric(
        columns[2],
        "Return Risk Outliers",
        number(
            stores[
                "IsReturnRiskOutlier"
            ].sum()
        ),
    )

    if candidates.empty:
        st.success(
            "No stores exceed the current "
            "2-standard-deviation screening threshold."
        )

        return

    st.dataframe(
        candidates[
            [
                "StoreCode",
                "StoreName",
                "EmirateName",
                "Revenue",
                "GrossMarginPct",
                "ReturnRatePct",
                "RevenueZScore",
                "MarginZScore",
                "ReturnZScore",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config=(
            dataframe_config()
        ),
    )


# ============================================================
# Data Explorer
# ============================================================

def _render_data_explorer(
    user,
    stores: pd.DataFrame,
    emirates: pd.DataFrame,
) -> None:
    section_header(
        "Store & Emirate Data Explorer",
        (
            "Filtered datasets used throughout "
            "the network dashboard."
        ),
    )

    store_tab, emirate_tab, risk_tab = (
        st.tabs(
            [
                "Store Performance",
                "Emirate Performance",
                "Management Flags",
            ]
        )
    )

    with store_tab:
        table = (
            stores.sort_values(
                "PerformanceScore",
                ascending=False,
            )
            .copy()
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=table,
            label=(
                "Export filtered "
                "store performance"
            ),
            file_name=(
                "stores_filtered_"
                "performance.csv"
            ),
            key=(
                "stores_export_performance"
            ),
        )

    with emirate_tab:
        st.dataframe(
            emirates,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=emirates,
            label=(
                "Export filtered "
                "emirate performance"
            ),
            file_name=(
                "emirates_filtered_"
                "performance.csv"
            ),
            key=(
                "stores_export_emirates"
            ),
        )

    with risk_tab:
        flagged = (
            stores[
                stores[
                    "AttentionFlag"
                ]
                != "Normal"
            ]
            .copy()
        )

        if flagged.empty:
            st.success(
                "No store management flags "
                "under the active filters."
            )

        else:
            st.dataframe(
                flagged[
                    [
                        "StoreCode",
                        "StoreName",
                        "EmirateName",
                        "Revenue",
                        "GrossProfit",
                        "GrossMarginPct",
                        "ReturnRatePct",
                        "PerformanceScore",
                        "AttentionFlag",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config=(
                    dataframe_config()
                ),
            )

            secure_csv_download(
                user=user,
                dataframe=flagged,
                label=(
                    "Export store "
                    "management flags"
                ),
                file_name=(
                    "store_management_"
                    "flags.csv"
                ),
                key=(
                    "stores_export_flags"
                ),
            )


# ============================================================
# Main
# ============================================================

def render(
    user,
    filters,
) -> None:
    page_header(
        "Stores & Emirates Command Center",
        (
            "Advanced UAE network intelligence covering "
            "store ranking, geographic contribution, "
            "profitability, customer economics, return "
            "risk, concentration and performance scoring."
        ),
        "UAE NETWORK INTELLIGENCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

    raw_stores = (
        get_filtered_store_performance(
            user,
            filters,
        )
    )

    raw_emirates = (
        get_filtered_emirate_performance(
            user,
            filters,
        )
    )

    if raw_stores.empty:
        st.warning(
            "No store performance data "
            "matches the active filters."
        )

        return

    stores = _prepare_stores(
        raw_stores
    )

    emirates = _prepare_emirates(
        raw_emirates,
        stores,
    )

    _render_network_kpis(
        stores,
        emirates,
    )

    _render_network_signals(
        stores
    )

    _render_emirate_analysis(
        emirates
    )

    _render_store_ranking(
        stores
    )

    _render_quadrants(
        stores
    )

    _render_performance_score(
        stores
    )

    _render_customer_economics(
        stores
    )

    _render_return_risk(
        stores
    )

    _render_concentration(
        stores
    )

    _render_outliers(
        stores
    )

    _render_data_explorer(
        user,
        stores,
        emirates,
    )