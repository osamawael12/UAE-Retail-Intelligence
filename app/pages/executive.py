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
    get_filtered_daily_sales,
    get_filtered_emirate_performance,
    get_filtered_monthly_sales,
    get_filtered_store_performance,
    get_filtered_summary,
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

    if not math.isfinite(result):
        return default

    return result


def _safe_growth(
    current,
    previous,
) -> float | None:
    current_value = _safe_float(
        current
    )

    previous_value = _safe_float(
        previous
    )

    if previous_value == 0:
        return None

    return (
        (
            current_value
            - previous_value
        )
        / abs(previous_value)
        * 100.0
    )


def _latest_non_null(
    dataframe: pd.DataFrame,
    column: str,
) -> float | None:
    if (
        dataframe.empty
        or column
        not in dataframe.columns
    ):
        return None

    values = (
        dataframe[column]
        .dropna()
    )

    if values.empty:
        return None

    return float(
        values.iloc[-1]
    )


def _tone(
    value,
    reverse: bool = False,
) -> str:
    numeric = _safe_float(
        value
    )

    if reverse:
        return (
            "green"
            if numeric <= 0
            else "red"
        )

    return (
        "green"
        if numeric >= 0
        else "red"
    )


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


def _prepare_monthly(
    monthly: pd.DataFrame,
) -> pd.DataFrame:
    data = monthly.copy()

    if data.empty:
        return data

    data = data.sort_values(
        "MonthStart"
    ).reset_index(
        drop=True
    )

    data[
        "Revenue3MMA"
    ] = (
        data["Revenue"]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Revenue6MMA"
    ] = (
        data["Revenue"]
        .rolling(
            6,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Profit3MMA"
    ] = (
        data["GrossProfit"]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
    )

    data[
        "RevenueIndex"
    ] = np.where(
        data["Revenue"].iloc[0] != 0,
        data["Revenue"]
        / data["Revenue"].iloc[0]
        * 100.0,
        np.nan,
    )

    data[
        "ProfitIndex"
    ] = np.where(
        data[
            "GrossProfit"
        ].iloc[0] != 0,
        data[
            "GrossProfit"
        ]
        / data[
            "GrossProfit"
        ].iloc[0]
        * 100.0,
        np.nan,
    )

    return data


def _prepare_daily(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    data = daily.copy()

    if data.empty:
        return data

    data = data.sort_values(
        "FullDate"
    ).reset_index(
        drop=True
    )

    data[
        "Revenue7DMA"
    ] = (
        data["Revenue"]
        .rolling(
            7,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Revenue30DMA"
    ] = (
        data["Revenue"]
        .rolling(
            30,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Revenue90DMA"
    ] = (
        data["Revenue"]
        .rolling(
            90,
            min_periods=1,
        )
        .mean()
    )

    data[
        "DayOfWeek"
    ] = data[
        "FullDate"
    ].dt.day_name()

    data[
        "MonthLabel"
    ] = data[
        "FullDate"
    ].dt.strftime(
        "%Y-%m"
    )

    return data


# ============================================================
# KPI Section
# ============================================================

def _render_primary_kpis(
    summary: dict,
    monthly: pd.DataFrame,
) -> None:
    latest_mom = (
        _latest_non_null(
            monthly,
            "MoMRevenuePct",
        )
    )

    latest_yoy = (
        _latest_non_null(
            monthly,
            "YoYRevenuePct",
        )
    )

    revenue = _safe_float(
        summary.get(
            "Revenue"
        )
    )

    profit = _safe_float(
        summary.get(
            "GrossProfit"
        )
    )

    orders = _safe_float(
        summary.get(
            "Orders"
        )
    )

    customers = _safe_float(
        summary.get(
            "Customers"
        )
    )

    section_header(
        "Executive KPI Pulse",
        (
            "Core commercial indicators for "
            "the current RLS scope and active "
            "analytical filters."
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Revenue",
        money(revenue),
        latest_yoy,
        (
            "Revenue after completed returns. "
            "Delta shows latest available YoY "
            "monthly growth."
        ),
    )

    metric(
        row[1],
        "Gross Profit",
        money(profit),
        help_text=(
            "Revenue less net COGS."
        ),
    )

    metric(
        row[2],
        "Gross Margin",
        percentage(
            summary.get(
                "GrossMarginPct"
            )
        ),
    )

    metric(
        row[3],
        "Orders",
        number(orders),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Customers",
        number(customers),
    )

    metric(
        row[1],
        "Average Order Value",
        money(
            summary.get(
                "AOV"
            )
        ),
    )

    metric(
        row[2],
        "Net Units",
        number(
            summary.get(
                "NetUnits"
            )
        ),
    )

    metric(
        row[3],
        "Return Rate",
        percentage(
            summary.get(
                "ReturnRatePct"
            )
        ),
    )

    revenue_per_customer = (
        revenue / customers
        if customers
        else 0
    )

    units_per_order = (
        _safe_float(
            summary.get(
                "NetUnits"
            )
        )
        / orders
        if orders
        else 0
    )

    second_row = st.columns(4)

    metric(
        second_row[0],
        "Revenue / Customer",
        money(
            revenue_per_customer
        ),
    )

    metric(
        second_row[1],
        "Net Units / Order",
        f"{units_per_order:.2f}",
    )

    metric(
        second_row[2],
        "Latest MoM",
        percentage(
            latest_mom,
            signed=True,
        )
        if latest_mom
        is not None
        else "N/A",
    )

    metric(
        second_row[3],
        "Latest YoY",
        percentage(
            latest_yoy,
            signed=True,
        )
        if latest_yoy
        is not None
        else "N/A",
    )


# ============================================================
# Executive Signals
# ============================================================

def _render_growth_signals(
    monthly: pd.DataFrame,
    daily: pd.DataFrame,
) -> None:
    if monthly.empty:
        return

    latest_mom = (
        _latest_non_null(
            monthly,
            "MoMRevenuePct",
        )
    )

    latest_yoy = (
        _latest_non_null(
            monthly,
            "YoYRevenuePct",
        )
    )

    best_month_row = (
        monthly.loc[
            monthly[
                "Revenue"
            ].idxmax()
        ]
    )

    worst_month_row = (
        monthly.loc[
            monthly[
                "Revenue"
            ].idxmin()
        ]
    )

    volatility = 0.0

    if (
        len(
            daily
        ) > 1
        and _safe_float(
            daily[
                "Revenue"
            ].mean()
        )
        != 0
    ):
        volatility = (
            _safe_float(
                daily[
                    "Revenue"
                ].std()
            )
            / _safe_float(
                daily[
                    "Revenue"
                ].mean()
            )
            * 100
        )

    section_header(
        "Executive Signals",
        (
            "Automatically derived commercial "
            "signals from the filtered dataset."
        ),
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "MOM MOMENTUM",
            (
                percentage(
                    latest_mom,
                    signed=True,
                )
                if latest_mom
                is not None
                else "N/A"
            ),
            (
                "Latest available month "
                "versus previous month."
            ),
            _tone(
                latest_mom
            ),
        )

    with columns[1]:
        insight_card(
            "YOY MOMENTUM",
            (
                percentage(
                    latest_yoy,
                    signed=True,
                )
                if latest_yoy
                is not None
                else "N/A"
            ),
            (
                "Latest available month "
                "versus same month prior year."
            ),
            _tone(
                latest_yoy
            ),
        )

    with columns[2]:
        insight_card(
            "PEAK MONTH",
            (
                best_month_row[
                    "MonthStart"
                ].strftime(
                    "%b %Y"
                )
            ),
            money(
                best_month_row[
                    "Revenue"
                ]
            ),
            "green",
        )

    with columns[3]:
        insight_card(
            "DAILY VOLATILITY",
            percentage(
                volatility
            ),
            (
                "Standard deviation as "
                "a share of mean daily revenue."
            ),
            (
                "green"
                if volatility < 30
                else "gold"
                if volatility < 50
                else "red"
            ),
        )

    columns = st.columns(2)

    with columns[0]:
        insight_card(
            "LOWEST MONTH",
            (
                worst_month_row[
                    "MonthStart"
                ].strftime(
                    "%b %Y"
                )
            ),
            money(
                worst_month_row[
                    "Revenue"
                ]
            ),
            "gold",
        )

    with columns[1]:
        if (
            len(monthly)
            >= 2
        ):
            start_revenue = (
                monthly[
                    "Revenue"
                ].iloc[0]
            )

            end_revenue = (
                monthly[
                    "Revenue"
                ].iloc[-1]
            )

            total_growth = (
                _safe_growth(
                    end_revenue,
                    start_revenue,
                )
            )

        else:
            total_growth = None

        insight_card(
            "PERIOD TRAJECTORY",
            (
                percentage(
                    total_growth,
                    signed=True,
                )
                if total_growth
                is not None
                else "N/A"
            ),
            (
                "First visible month "
                "to latest visible month."
            ),
            _tone(
                total_growth
            ),
        )


# ============================================================
# Revenue Trend
# ============================================================

def _render_revenue_trends(
    monthly: pd.DataFrame,
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Revenue & Profit Trajectory",
        (
            "Monthly commercial performance "
            "with rolling trend diagnostics."
        ),
    )

    left, right = st.columns(
        [1.6, 1]
    )

    with left:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "Revenue"
                ],
                mode="lines+markers",
                name="Revenue",
                line=dict(
                    color=COLORS[
                        "uae_green"
                    ],
                    width=3,
                ),
                marker=dict(
                    size=6,
                ),
            )
        )

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "Revenue3MMA"
                ],
                mode="lines",
                name="3M Moving Average",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=2.5,
                ),
            )
        )

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "Revenue6MMA"
                ],
                mode="lines",
                name="6M Moving Average",
                line=dict(
                    color=COLORS[
                        "info"
                    ],
                    width=2,
                    dash="dot",
                ),
            )
        )

        figure.update_layout(
            title=(
                "Monthly Revenue & "
                "Moving Averages"
            ),
            xaxis_title=None,
            yaxis_title="AED",
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )

    with right:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "GrossProfit"
                ],
                mode="lines+markers",
                name="Gross Profit",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=3,
                ),
            )
        )

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "Profit3MMA"
                ],
                mode="lines",
                name=(
                    "3M Profit Average"
                ),
                line=dict(
                    color=COLORS[
                        "uae_green"
                    ],
                    width=2,
                ),
            )
        )

        figure.update_layout(
            title=(
                "Gross Profit Trend"
            ),
            xaxis_title=None,
            yaxis_title="AED",
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )

    section_header(
        "Short-Term Operating Trend",
        (
            "Daily revenue with 7, 30 and "
            "90-day moving averages."
        ),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=daily[
                "FullDate"
            ],
            y=daily[
                "Revenue"
            ],
            name="Daily Revenue",
            mode="lines",
            line=dict(
                color=(
                    "rgba(58,158,232,.20)"
                ),
                width=1,
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=daily[
                "FullDate"
            ],
            y=daily[
                "Revenue7DMA"
            ],
            name="7D",
            line=dict(
                color=COLORS[
                    "info"
                ],
                width=1.5,
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=daily[
                "FullDate"
            ],
            y=daily[
                "Revenue30DMA"
            ],
            name="30D",
            line=dict(
                color=COLORS[
                    "uae_green"
                ],
                width=3,
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=daily[
                "FullDate"
            ],
            y=daily[
                "Revenue90DMA"
            ],
            name="90D",
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=2.2,
                dash="dash",
            ),
        )
    )

    figure.update_layout(
        title=(
            "Daily Revenue Trend"
        ),
        xaxis_title=None,
        yaxis_title="AED",
    )

    st.plotly_chart(
        style_figure(
            figure,
            480,
        ),
        use_container_width=True,
    )


# ============================================================
# Growth Diagnostics
# ============================================================

def _render_growth_diagnostics(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Growth Diagnostics",
        (
            "MoM and YoY momentum, indexed growth "
            "and margin progression."
        ),
    )

    left, right = st.columns(2)

    with left:
        growth = (
            monthly[
                [
                    "MonthStart",
                    "MoMRevenuePct",
                    "YoYRevenuePct",
                ]
            ]
            .melt(
                id_vars=[
                    "MonthStart"
                ],
                var_name="Metric",
                value_name="GrowthPct",
            )
        )

        figure = px.bar(
            growth,
            x="MonthStart",
            y="GrowthPct",
            color="Metric",
            barmode="group",
            title=(
                "MoM vs YoY Revenue Growth"
            ),
            color_discrete_map={
                "MoMRevenuePct":
                    COLORS["gold"],
                "YoYRevenuePct":
                    COLORS[
                        "uae_green"
                    ],
            },
        )

        figure.add_hline(
            y=0,
            line_dash="dot",
            line_color=(
                COLORS["muted"]
            ),
        )

        figure.update_layout(
            xaxis_title=None,
            yaxis_title="Growth %",
            legend_title=None,
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    with right:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "RevenueIndex"
                ],
                name="Revenue Index",
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "uae_green"
                    ],
                    width=3,
                ),
            )
        )

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "ProfitIndex"
                ],
                name="Profit Index",
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=2.5,
                ),
            )
        )

        figure.add_hline(
            y=100,
            line_dash="dot",
            line_color=(
                COLORS["muted"]
            ),
        )

        figure.update_layout(
            title=(
                "Indexed Performance "
                "(First Month = 100)"
            ),
            xaxis_title=None,
            yaxis_title="Index",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    figure = px.scatter(
        monthly,
        x="Revenue",
        y="GrossMarginPct",
        size="Orders",
        color="MoMRevenuePct",
        hover_name=(
            monthly[
                "MonthStart"
            ].dt.strftime(
                "%b %Y"
            )
        ),
        title=(
            "Monthly Revenue / Margin Matrix"
        ),
        color_continuous_scale=[
            COLORS["uae_red"],
            COLORS["gold"],
            COLORS["uae_green"],
        ],
        color_continuous_midpoint=0,
    )

    st.plotly_chart(
        style_figure(
            figure,
            440,
        ),
        use_container_width=True,
    )


# ============================================================
# Day of Week Analysis
# ============================================================

def _render_weekday_analysis(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Trading Week Intelligence",
        (
            "Average daily demand and consistency "
            "across days of the week."
        ),
    )

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    weekday = (
        daily.groupby(
            "DayOfWeek",
            as_index=False,
        )
        .agg(
            AvgDailyRevenue=(
                "Revenue",
                "mean",
            ),
            TotalRevenue=(
                "Revenue",
                "sum",
            ),
            AvgDailyOrders=(
                "Orders",
                "mean",
            ),
            RevenueVolatility=(
                "Revenue",
                "std",
            ),
        )
    )

    weekday[
        "DayOfWeek"
    ] = pd.Categorical(
        weekday[
            "DayOfWeek"
        ],
        categories=(
            weekday_order
        ),
        ordered=True,
    )

    weekday = (
        weekday.sort_values(
            "DayOfWeek"
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            weekday,
            x="DayOfWeek",
            y="AvgDailyRevenue",
            color="AvgDailyRevenue",
            title=(
                "Average Revenue "
                "by Day of Week"
            ),
            color_continuous_scale=[
                COLORS[
                    "surface3"
                ],
                COLORS["gold"],
                COLORS[
                    "uae_green"
                ],
            ],
        )

        figure.update_layout(
            coloraxis_showscale=False,
            xaxis_title=None,
            yaxis_title=(
                "Average Daily Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            weekday,
            x="AvgDailyOrders",
            y="AvgDailyRevenue",
            size="RevenueVolatility",
            color="DayOfWeek",
            hover_name="DayOfWeek",
            title=(
                "Demand / Revenue "
                "Trading Profile"
            ),
        )

        figure.update_layout(
            xaxis_title=(
                "Average Daily Orders"
            ),
            yaxis_title=(
                "Average Daily Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )


# ============================================================
# Emirates
# ============================================================

def _render_emirate_intelligence(
    emirates: pd.DataFrame,
) -> None:
    if emirates.empty:
        return

    section_header(
        "UAE Geographic Intelligence",
        (
            "Revenue contribution, margin quality, "
            "customer scale and store productivity "
            "across visible emirates."
        ),
    )

    data = emirates.copy()

    total_revenue = _safe_float(
        data[
            "Revenue"
        ].sum()
    )

    data[
        "RevenueSharePct"
    ] = (
        data["Revenue"]
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    data[
        "RevenuePerStore"
    ] = np.where(
        data["Stores"] != 0,
        data["Revenue"]
        / data["Stores"],
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

    left, right = st.columns(
        [1.1, 1]
    )

    with left:
        figure = px.bar(
            data.sort_values(
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
            title=(
                "Revenue Contribution "
                "by Emirate"
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
                440,
                legend=False,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            data,
            x="Revenue",
            y="GrossMarginPct",
            size="Customers",
            color="EmirateName",
            hover_name="EmirateName",
            hover_data=[
                "Stores",
                "Orders",
                "RevenuePerStore",
                "RevenuePerCustomer",
            ],
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            title=(
                "Emirate Value Matrix"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    figure = px.bar(
        data.sort_values(
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
        xaxis_title=(
            "Revenue per Store"
        ),
        yaxis_title=None,
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
# Store Portfolio
# ============================================================

def _render_store_intelligence(
    stores: pd.DataFrame,
) -> None:
    if stores.empty:
        return

    section_header(
        "Store Portfolio Intelligence",
        (
            "Store ranking, concentration, profitability, "
            "return risk and performance quadrants."
        ),
    )

    data = stores.copy()

    median_revenue = _safe_float(
        data[
            "Revenue"
        ].median()
    )

    median_margin = _safe_float(
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
            "High Revenue / High Margin",
            "High Revenue / Margin Pressure",
            "Lower Revenue / High Margin",
        ],
        default=(
            "Lower Revenue / Lower Margin"
        ),
    )

    left, right = st.columns(2)

    with left:
        top = (
            data.nlargest(
                min(
                    12,
                    len(data),
                ),
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
                "GrossMarginPct",
                "AOV",
            ],
            title=(
                "Top Stores by Revenue"
            ),
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
            data,
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
                "RevenueSharePct",
            ],
            title=(
                "Store Revenue / Margin Quadrants"
            ),
            color_discrete_map={
                (
                    "High Revenue / "
                    "High Margin"
                ):
                    COLORS[
                        "uae_green"
                    ],

                (
                    "High Revenue / "
                    "Margin Pressure"
                ):
                    COLORS["gold"],

                (
                    "Lower Revenue / "
                    "High Margin"
                ):
                    COLORS["info"],

                (
                    "Lower Revenue / "
                    "Lower Margin"
                ):
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        figure.add_vline(
            x=median_revenue,
            line_dash="dash",
            opacity=.5,
        )

        figure.add_hline(
            y=median_margin,
            line_dash="dash",
            opacity=.5,
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )

    left, right = st.columns(2)

    with left:
        return_risk = (
            data.nlargest(
                min(
                    12,
                    len(data),
                ),
                "ReturnRatePct",
            )
            .sort_values(
                "ReturnRatePct"
            )
        )

        figure = px.bar(
            return_risk,
            x="ReturnRatePct",
            y="StoreCode",
            orientation="h",
            color="ReturnRatePct",
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
                440,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            data,
            x="AOV",
            y="Revenue",
            size="Customers",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_name="StoreName",
            hover_data=[
                "StoreCode",
                "Orders",
            ],
            title=(
                "AOV / Revenue / "
                "Customer Scale"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    total_revenue = _safe_float(
        data[
            "Revenue"
        ].sum()
    )

    top5_revenue = _safe_float(
        data.nlargest(
            min(
                5,
                len(data),
            ),
            "Revenue",
        )[
            "Revenue"
        ].sum()
    )

    concentration = (
        top5_revenue
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    section_header(
        "Portfolio Concentration"
    )

    concentration_columns = (
        st.columns(3)
    )

    metric(
        concentration_columns[0],
        "Top 5 Revenue Share",
        percentage(
            concentration
        ),
    )

    metric(
        concentration_columns[1],
        "Median Store Revenue",
        money(
            data[
                "Revenue"
            ].median()
        ),
    )

    metric(
        concentration_columns[2],
        "Median Store Margin",
        percentage(
            data[
                "GrossMarginPct"
            ].median()
        ),
    )


# ============================================================
# Period Comparison
# ============================================================

def _render_period_comparison(
    daily: pd.DataFrame,
) -> None:
    if len(daily) < 2:
        return

    section_header(
        "Period-on-Period Comparison",
        (
            "Compares equal-duration halves of the "
            "currently visible daily dataset."
        ),
    )

    midpoint = (
        len(daily) // 2
    )

    first = (
        daily.iloc[
            :midpoint
        ]
    )

    second = (
        daily.iloc[
            midpoint:
        ]
    )

    compare_length = min(
        len(first),
        len(second),
    )

    if compare_length <= 0:
        return

    first = (
        first.tail(
            compare_length
        )
    )

    second = (
        second.tail(
            compare_length
        )
    )

    metrics = []

    definitions = [
        (
            "Revenue",
            "Revenue",
        ),
        (
            "Gross Profit",
            "GrossProfit",
        ),
        (
            "Orders",
            "Orders",
        ),
        (
            "Customers",
            "Customers",
        ),
        (
            "Net Units",
            "NetUnits",
        ),
    ]

    for label, column in (
        definitions
    ):
        previous_value = (
            first[
                column
            ].sum()
        )

        current_value = (
            second[
                column
            ].sum()
        )

        growth = _safe_growth(
            current_value,
            previous_value,
        )

        metrics.append(
            {
                "Metric":
                    label,

                "PreviousPeriod":
                    previous_value,

                "CurrentPeriod":
                    current_value,

                "GrowthPct":
                    growth,
            }
        )

    comparison = (
        pd.DataFrame(
            metrics
        )
    )

    figure = px.bar(
        comparison,
        x="Metric",
        y="GrowthPct",
        color="GrowthPct",
        title=(
            "Equal-Period Growth Comparison"
        ),
        color_continuous_scale=[
            COLORS["uae_red"],
            COLORS["gold"],
            COLORS["uae_green"],
        ],
        color_continuous_midpoint=0,
    )

    figure.add_hline(
        y=0,
        line_dash="dot",
    )

    figure.update_layout(
        coloraxis_showscale=False,
        yaxis_title="Growth %",
        xaxis_title=None,
    )

    st.plotly_chart(
        style_figure(
            figure,
            400,
        ),
        use_container_width=True,
    )


# ============================================================
# Executive Risk Radar
# ============================================================

def _render_risk_radar(
    stores: pd.DataFrame,
    monthly: pd.DataFrame,
) -> None:
    if (
        stores.empty
        or monthly.empty
    ):
        return

    section_header(
        "Executive Risk Radar",
        (
            "Relative operating indicators designed "
            "to highlight portfolio attention areas."
        ),
    )

    revenue_growth = (
        _latest_non_null(
            monthly,
            "YoYRevenuePct",
        )
    )

    median_margin = (
        _safe_float(
            stores[
                "GrossMarginPct"
            ].median()
        )
    )

    median_returns = (
        _safe_float(
            stores[
                "ReturnRatePct"
            ].median()
        )
    )

    revenue_cv = 0.0

    monthly_mean = (
        _safe_float(
            monthly[
                "Revenue"
            ].mean()
        )
    )

    if monthly_mean:
        revenue_cv = (
            _safe_float(
                monthly[
                    "Revenue"
                ].std()
            )
            / monthly_mean
            * 100
        )

    top3_share = 0.0

    total_revenue = (
        _safe_float(
            stores[
                "Revenue"
            ].sum()
        )
    )

    if total_revenue:
        top3_share = (
            _safe_float(
                stores.nlargest(
                    min(
                        3,
                        len(stores),
                    ),
                    "Revenue",
                )[
                    "Revenue"
                ].sum()
            )
            / total_revenue
            * 100
        )

    categories = [
        "Growth",
        "Margin",
        "Return Health",
        "Revenue Stability",
        "Diversification",
    ]

    growth_score = (
        np.clip(
            50
            + _safe_float(
                revenue_growth
            ),
            0,
            100,
        )
    )

    margin_score = (
        np.clip(
            median_margin
            * 2,
            0,
            100,
        )
    )

    return_score = (
        np.clip(
            100
            - median_returns
            * 5,
            0,
            100,
        )
    )

    stability_score = (
        np.clip(
            100
            - revenue_cv,
            0,
            100,
        )
    )

    diversification_score = (
        np.clip(
            100
            - top3_share,
            0,
            100,
        )
    )

    values = [
        growth_score,
        margin_score,
        return_score,
        stability_score,
        diversification_score,
    ]

    categories_closed = (
        categories
        + [categories[0]]
    )

    values_closed = (
        values
        + [values[0]]
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            name="Portfolio Score",
            line=dict(
                color=COLORS[
                    "uae_green"
                ],
                width=3,
            ),
            fillcolor=(
                "rgba(0,132,61,.14)"
            ),
        )
    )

    figure.update_layout(
        title=(
            "Executive Portfolio Health Radar"
        ),
        polar=dict(
            bgcolor=(
                "rgba(0,0,0,0)"
            ),
            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    100,
                ],
                gridcolor=(
                    "rgba(143,165,185,.13)"
                ),
            ),
            angularaxis=dict(
                gridcolor=(
                    "rgba(143,165,185,.13)"
                ),
            ),
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            470,
            legend=False,
        ),
        use_container_width=True,
    )

    st.caption(
        "Radar scores are relative management "
        "indicators for dashboard triage, not "
        "formal financial risk ratings."
    )


# ============================================================
# Tables and Export
# ============================================================

def _render_tables(
    user,
    monthly: pd.DataFrame,
    emirates: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Executive Data Explorer",
        (
            "Detailed filtered datasets used by "
            "the executive dashboard."
        ),
    )

    tab_store, tab_emirate, tab_month = (
        st.tabs(
            [
                "Stores",
                "Emirates",
                "Monthly",
            ]
        )
    )

    with tab_store:
        display = (
            stores.sort_values(
                "Revenue",
                ascending=False,
            )
            .copy()
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=display,
            label=(
                "Export filtered "
                "store performance"
            ),
            file_name=(
                "executive_store_"
                "performance.csv"
            ),
            key=(
                "executive_export_stores"
            ),
        )

    with tab_emirate:
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
                "executive_emirate_"
                "performance.csv"
            ),
            key=(
                "executive_export_emirates"
            ),
        )

    with tab_month:
        st.dataframe(
            monthly,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=monthly,
            label=(
                "Export filtered "
                "monthly performance"
            ),
            file_name=(
                "executive_monthly_"
                "performance.csv"
            ),
            key=(
                "executive_export_monthly"
            ),
        )


# ============================================================
# Main Page
# ============================================================

def render(
    user,
    filters,
) -> None:
    page_header(
        "Executive Command Center",
        (
            "Enterprise performance cockpit covering "
            "revenue, profitability, growth, customers, "
            "UAE geography, stores and management risk "
            "signals within the authorized RLS scope."
        ),
        "UAE EXECUTIVE INTELLIGENCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

    # --------------------------------------------------------
    # Load all executive datasets
    # --------------------------------------------------------

    summary = (
        get_filtered_summary(
            user,
            filters,
        )
    )

    monthly = (
        get_filtered_monthly_sales(
            user,
            filters,
        )
    )

    daily = (
        get_filtered_daily_sales(
            user,
            filters,
        )
    )

    emirates = (
        get_filtered_emirate_performance(
            user,
            filters,
        )
    )

    stores = (
        get_filtered_store_performance(
            user,
            filters,
        )
    )

    # --------------------------------------------------------
    # Empty-state handling
    # --------------------------------------------------------

    revenue = _safe_float(
        summary.get(
            "Revenue"
        )
    )

    if (
        revenue == 0
        and monthly.empty
        and stores.empty
    ):
        st.warning(
            "No commercial data matches "
            "the active analytical filters."
        )

        return

    # --------------------------------------------------------
    # Preparation
    # --------------------------------------------------------

    monthly = _prepare_monthly(
        monthly
    )

    daily = _prepare_daily(
        daily
    )

    # --------------------------------------------------------
    # Dashboard sections
    # --------------------------------------------------------

    _render_primary_kpis(
        summary,
        monthly,
    )

    _render_growth_signals(
        monthly,
        daily,
    )

    if (
        not monthly.empty
        and not daily.empty
    ):
        _render_revenue_trends(
            monthly,
            daily,
        )

        _render_growth_diagnostics(
            monthly,
        )

        _render_weekday_analysis(
            daily,
        )

        _render_period_comparison(
            daily,
        )

    _render_emirate_intelligence(
        emirates
    )

    _render_store_intelligence(
        stores
    )

    _render_risk_radar(
        stores,
        monthly,
    )

    _render_tables(
        user,
        monthly,
        emirates,
        stores,
    )