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
from app.theme import COLORS
from src.analytics.filtered_data import (
    get_filtered_daily_sales,
    get_filtered_monthly_sales,
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

    if not math.isfinite(
        result
    ):
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
        / abs(
            previous_value
        )
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

    series = (
        dataframe[
            column
        ]
        .dropna()
    )

    if series.empty:
        return None

    return float(
        series.iloc[-1]
    )


def _tone(
    value,
) -> str:
    if value is None:
        return "gold"

    return (
        "green"
        if _safe_float(value) >= 0
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

    return (
        "Full available history"
    )


# ============================================================
# Data Preparation
# ============================================================

def _prepare_daily(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    data = (
        dataframe.copy()
    )

    if data.empty:
        return data

    data = (
        data.sort_values(
            "FullDate"
        )
        .reset_index(
            drop=True
        )
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
        "Profit30DMA"
    ] = (
        data[
            "GrossProfit"
        ]
        .rolling(
            30,
            min_periods=1,
        )
        .mean()
    )

    data[
        "DayOfWeek"
    ] = (
        data["FullDate"]
        .dt.day_name()
    )

    data[
        "DayOfWeekNumber"
    ] = (
        data["FullDate"]
        .dt.dayofweek
    )

    data[
        "MonthNumber"
    ] = (
        data["FullDate"]
        .dt.month
    )

    data[
        "MonthName"
    ] = (
        data["FullDate"]
        .dt.month_name()
    )

    data[
        "Year"
    ] = (
        data["FullDate"]
        .dt.year
    )

    data[
        "Quarter"
    ] = (
        "Q"
        + data["FullDate"]
        .dt.quarter
        .astype(str)
    )

    data[
        "YearMonth"
    ] = (
        data["FullDate"]
        .dt.to_period("M")
        .astype(str)
    )

    data[
        "AOV"
    ] = np.where(
        data["Orders"] != 0,
        data["Revenue"]
        / data["Orders"],
        0,
    )

    data[
        "GrossMarginPct"
    ] = np.where(
        data["Revenue"] != 0,
        data["GrossProfit"]
        * 100
        / data["Revenue"],
        0,
    )

    data[
        "ReturnRatePct"
    ] = np.where(
        data[
            "GrossUnits"
        ] != 0,
        data[
            "ReturnedUnits"
        ]
        * 100
        / data[
            "GrossUnits"
        ],
        0,
    )

    data[
        "DailyRevenueChangePct"
    ] = (
        data["Revenue"]
        .pct_change(
            fill_method=None
        )
        * 100
    )

    rolling_mean = (
        data["Revenue"]
        .rolling(
            30,
            min_periods=10,
        )
        .mean()
    )

    rolling_std = (
        data["Revenue"]
        .rolling(
            30,
            min_periods=10,
        )
        .std()
    )

    data[
        "RevenueZScore30D"
    ] = np.where(
        rolling_std != 0,
        (
            data["Revenue"]
            - rolling_mean
        )
        / rolling_std,
        np.nan,
    )

    return data


def _prepare_monthly(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    data = (
        dataframe.copy()
    )

    if data.empty:
        return data

    data = (
        data.sort_values(
            "MonthStart"
        )
        .reset_index(
            drop=True
        )
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
        "Revenue12MMA"
    ] = (
        data["Revenue"]
        .rolling(
            12,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Profit3MMA"
    ] = (
        data[
            "GrossProfit"
        ]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
    )

    data[
        "Year"
    ] = (
        data[
            "MonthStart"
        ]
        .dt.year
    )

    data[
        "Month"
    ] = (
        data[
            "MonthStart"
        ]
        .dt.month
    )

    data[
        "MonthName"
    ] = (
        data[
            "MonthStart"
        ]
        .dt.month_name()
    )

    data[
        "Quarter"
    ] = (
        "Q"
        + data[
            "MonthStart"
        ]
        .dt.quarter
        .astype(str)
    )

    data[
        "RevenueContributionPct"
    ] = (
        data["Revenue"]
        / data[
            "Revenue"
        ].sum()
        * 100
        if data[
            "Revenue"
        ].sum()
        else 0
    )

    return data


# ============================================================
# KPI Header
# ============================================================

def _render_kpis(
    summary: dict,
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Commercial KPI Pulse",
        (
            "Filtered sales performance under "
            "the active SQL Server RLS scope."
        ),
    )

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

    row = st.columns(4)

    metric(
        row[0],
        "Revenue",
        money(
            summary.get(
                "Revenue"
            )
        ),
        latest_yoy,
    )

    metric(
        row[1],
        "Gross Profit",
        money(
            summary.get(
                "GrossProfit"
            )
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
        number(
            summary.get(
                "Orders"
            )
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Customers",
        number(
            summary.get(
                "Customers"
            )
        ),
    )

    metric(
        row[1],
        "AOV",
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

    row = st.columns(2)

    with row[0]:
        insight_card(
            "LATEST MOM REVENUE",
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
                "versus prior month."
            ),
            _tone(
                latest_mom
            ),
        )

    with row[1]:
        insight_card(
            "LATEST YOY REVENUE",
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


# ============================================================
# Monthly Trends
# ============================================================

def _render_monthly_trends(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Revenue & Profit Trend",
        (
            "Monthly performance with short, medium "
            "and annual rolling trend indicators."
        ),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=monthly[
                "MonthStart"
            ],
            y=monthly[
                "Revenue"
            ],
            name="Revenue",
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
                "Revenue3MMA"
            ],
            name="3M Average",
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
                "Revenue12MMA"
            ],
            name="12M Average",
            line=dict(
                color=COLORS[
                    "info"
                ],
                width=2,
                dash="dash",
            ),
        )
    )

    figure.update_layout(
        title=(
            "Monthly Revenue "
            "with Rolling Averages"
        ),
        yaxis_title="AED",
        xaxis_title=None,
    )

    st.plotly_chart(
        style_figure(
            figure,
            500,
        ),
        use_container_width=True,
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "GrossProfit"
                ],
                name="Gross Profit",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=3,
                ),
                mode="lines+markers",
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
                name="3M Profit Average",
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
                    "GrossMarginPct"
                ],
                name="Gross Margin %",
                line=dict(
                    color=COLORS[
                        "uae_green"
                    ],
                    width=3,
                ),
                mode="lines+markers",
            )
        )

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "ReturnRatePct"
                ],
                name="Return Rate %",
                line=dict(
                    color=COLORS[
                        "uae_red"
                    ],
                    width=2,
                ),
                mode="lines+markers",
            )
        )

        figure.update_layout(
            title=(
                "Margin vs Return Rate"
            ),
            xaxis_title=None,
            yaxis_title="Percent",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )


# ============================================================
# Growth Analysis
# ============================================================

def _render_growth(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "MoM & YoY Growth Intelligence",
        (
            "Momentum diagnostics to separate "
            "short-term movement from annual growth."
        ),
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.bar(
            monthly,
            x="MonthStart",
            y="MoMRevenuePct",
            color="MoMRevenuePct",
            title=(
                "Month-on-Month "
                "Revenue Growth"
            ),
            color_continuous_scale=[
                COLORS[
                    "uae_red"
                ],
                COLORS["gold"],
                COLORS[
                    "uae_green"
                ],
            ],
            color_continuous_midpoint=0,
        )

        figure.add_hline(
            y=0,
            line_dash="dot",
        )

        figure.update_layout(
            coloraxis_showscale=False,
            xaxis_title=None,
            yaxis_title="MoM %",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            monthly,
            x="MonthStart",
            y="YoYRevenuePct",
            color="YoYRevenuePct",
            title=(
                "Year-on-Year "
                "Revenue Growth"
            ),
            color_continuous_scale=[
                COLORS[
                    "uae_red"
                ],
                COLORS["gold"],
                COLORS[
                    "uae_green"
                ],
            ],
            color_continuous_midpoint=0,
        )

        figure.add_hline(
            y=0,
            line_dash="dot",
        )

        figure.update_layout(
            coloraxis_showscale=False,
            xaxis_title=None,
            yaxis_title="YoY %",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    growth_scatter = (
        monthly.dropna(
            subset=[
                "MoMRevenuePct",
                "YoYRevenuePct",
            ]
        )
    )

    if not growth_scatter.empty:
        figure = px.scatter(
            growth_scatter,
            x="MoMRevenuePct",
            y="YoYRevenuePct",
            size="Revenue",
            color="GrossMarginPct",
            hover_name=(
                growth_scatter[
                    "MonthStart"
                ]
                .dt.strftime(
                    "%b %Y"
                )
            ),
            title=(
                "Growth Regime Matrix"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        figure.add_vline(
            x=0,
            line_dash="dash",
        )

        figure.add_hline(
            y=0,
            line_dash="dash",
        )

        figure.update_layout(
            xaxis_title="MoM Growth %",
            yaxis_title="YoY Growth %",
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
            ),
            use_container_width=True,
        )


# ============================================================
# Daily Performance
# ============================================================

def _render_daily_trend(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Daily Trading Performance",
        (
            "Daily revenue with short and long "
            "moving averages for operating momentum."
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
            line=dict(
                color=(
                    "rgba(58,158,232,.22)"
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
            name="7-Day Average",
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
            name="30-Day Average",
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
            name="90-Day Average",
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=2,
                dash="dash",
            ),
        )
    )

    figure.update_layout(
        title=(
            "Daily Revenue "
            "and Moving Averages"
        ),
        xaxis_title=None,
        yaxis_title="Revenue",
    )

    st.plotly_chart(
        style_figure(
            figure,
            480,
        ),
        use_container_width=True,
    )


# ============================================================
# Weekday Analysis
# ============================================================

def _render_weekday_analysis(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Day-of-Week Intelligence",
        (
            "Trading demand, AOV, margin and volatility "
            "across the weekly cycle."
        ),
    )

    order = [
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
            Days=(
                "FullDate",
                "count",
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
            AvgDailyRevenue=(
                "Revenue",
                "mean",
            ),
            RevenueStd=(
                "Revenue",
                "std",
            ),
            AvgOrders=(
                "Orders",
                "mean",
            ),
            AvgAOV=(
                "AOV",
                "mean",
            ),
            AvgMarginPct=(
                "GrossMarginPct",
                "mean",
            ),
            AvgReturnRatePct=(
                "ReturnRatePct",
                "mean",
            ),
        )
    )

    weekday[
        "DayOfWeek"
    ] = pd.Categorical(
        weekday[
            "DayOfWeek"
        ],
        categories=order,
        ordered=True,
    )

    weekday = (
        weekday.sort_values(
            "DayOfWeek"
        )
    )

    weekday[
        "CoefficientOfVariationPct"
    ] = np.where(
        weekday[
            "AvgDailyRevenue"
        ] != 0,
        weekday[
            "RevenueStd"
        ]
        / weekday[
            "AvgDailyRevenue"
        ]
        * 100,
        0,
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.bar(
            weekday,
            x="DayOfWeek",
            y="AvgDailyRevenue",
            color="AvgDailyRevenue",
            title=(
                "Average Daily Revenue "
                "by Weekday"
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
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            weekday,
            x="AvgOrders",
            y="AvgAOV",
            size="AvgDailyRevenue",
            color="AvgMarginPct",
            hover_name="DayOfWeek",
            hover_data=[
                "AvgReturnRatePct",
                "CoefficientOfVariationPct",
            ],
            title=(
                "Order Volume vs AOV"
            ),
            color_continuous_scale=(
                "RdYlGn"
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
# Seasonality
# ============================================================

def _render_seasonality(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Calendar Seasonality",
        (
            "Month-of-year and quarterly demand patterns "
            "across all visible years."
        ),
    )

    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    seasonal = (
        daily.groupby(
            [
                "MonthNumber",
                "MonthName",
            ],
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
            AvgOrders=(
                "Orders",
                "mean",
            ),
            AvgMarginPct=(
                "GrossMarginPct",
                "mean",
            ),
        )
        .sort_values(
            "MonthNumber"
        )
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.line(
            seasonal,
            x="MonthName",
            y="AvgDailyRevenue",
            markers=True,
            title=(
                "Month-of-Year "
                "Revenue Seasonality"
            ),
        )

        figure.update_traces(
            line=dict(
                color=COLORS[
                    "uae_green"
                ],
                width=3,
            ),
            marker=dict(
                size=8,
                color=COLORS[
                    "gold"
                ],
            ),
        )

        figure.update_xaxes(
            categoryorder="array",
            categoryarray=(
                month_order
            ),
        )

        figure.update_layout(
            xaxis_title=None,
            yaxis_title=(
                "Average Daily Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    with right:
        quarter = (
            daily.groupby(
                "Quarter",
                as_index=False,
            )
            .agg(
                Revenue=(
                    "Revenue",
                    "sum",
                ),
                GrossProfit=(
                    "GrossProfit",
                    "sum",
                ),
                Orders=(
                    "Orders",
                    "sum",
                ),
            )
        )

        figure = px.bar(
            quarter,
            x="Quarter",
            y="Revenue",
            color="GrossProfit",
            title=(
                "Quarterly Revenue"
            ),
            color_continuous_scale=[
                COLORS["gold"],
                COLORS[
                    "uae_green"
                ],
            ],
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )


# ============================================================
# Annual Analysis
# ============================================================

def _render_annual_performance(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Annual Performance",
        (
            "Year-level revenue, profit, customers "
            "and annual growth."
        ),
    )

    annual = (
        daily.groupby(
            "Year",
            as_index=False,
        )
        .agg(
            Revenue=(
                "Revenue",
                "sum",
            ),
            GrossProfit=(
                "GrossProfit",
                "sum",
            ),
            Orders=(
                "Orders",
                "sum",
            ),
            Customers=(
                "Customers",
                "sum",
            ),
            NetUnits=(
                "NetUnits",
                "sum",
            ),
        )
    )

    annual[
        "YoYGrowthPct"
    ] = (
        annual["Revenue"]
        .pct_change(
            fill_method=None
        )
        * 100
    )

    annual[
        "GrossMarginPct"
    ] = np.where(
        annual["Revenue"] != 0,
        annual[
            "GrossProfit"
        ]
        * 100
        / annual["Revenue"],
        0,
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.bar(
            annual,
            x="Year",
            y="Revenue",
            color="YoYGrowthPct",
            text_auto=".3s",
            title=(
                "Annual Revenue & YoY Growth"
            ),
            color_continuous_scale=[
                COLORS[
                    "uae_red"
                ],
                COLORS["gold"],
                COLORS[
                    "uae_green"
                ],
            ],
            color_continuous_midpoint=0,
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            annual,
            x="Revenue",
            y="GrossMarginPct",
            size="Orders",
            color="Year",
            hover_data=[
                "GrossProfit",
                "NetUnits",
            ],
            title=(
                "Annual Revenue / "
                "Margin Position"
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
# Anomalies
# ============================================================

def _render_anomaly_analysis(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Revenue Anomaly Candidates",
        (
            "Statistical screening using a rolling "
            "30-day revenue z-score. Candidates are "
            "signals for review, not confirmed anomalies."
        ),
    )

    anomalies = (
        daily[
            daily[
                "RevenueZScore30D"
            ]
            .abs()
            >= 2.0
        ]
        .copy()
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
            mode="lines",
            name="Daily Revenue",
            line=dict(
                color=(
                    "rgba(58,158,232,.34)"
                ),
            ),
        )
    )

    if not anomalies.empty:
        figure.add_trace(
            go.Scatter(
                x=anomalies[
                    "FullDate"
                ],
                y=anomalies[
                    "Revenue"
                ],
                mode="markers",
                name="Anomaly Candidate",
                marker=dict(
                    color=COLORS[
                        "uae_red"
                    ],
                    size=9,
                    symbol="diamond",
                ),
                customdata=(
                    anomalies[
                        [
                            "RevenueZScore30D",
                            "Orders",
                            "AOV",
                        ]
                    ]
                ),
                hovertemplate=(
                    "Date: %{x}<br>"
                    "Revenue: %{y:,.0f}<br>"
                    "Z-score: "
                    "%{customdata[0]:.2f}<br>"
                    "Orders: "
                    "%{customdata[1]:,.0f}<br>"
                    "AOV: "
                    "%{customdata[2]:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title=(
            "Daily Revenue "
            "Anomaly Screening"
        ),
        xaxis_title=None,
        yaxis_title="Revenue",
    )

    st.plotly_chart(
        style_figure(
            figure,
            450,
        ),
        use_container_width=True,
    )

    columns = st.columns(3)

    metric(
        columns[0],
        "Candidate Days",
        number(
            len(anomalies)
        ),
    )

    metric(
        columns[1],
        "Positive Candidates",
        number(
            (
                anomalies[
                    "RevenueZScore30D"
                ]
                >= 2
            ).sum()
        ),
    )

    metric(
        columns[2],
        "Negative Candidates",
        number(
            (
                anomalies[
                    "RevenueZScore30D"
                ]
                <= -2
            ).sum()
        ),
    )


# ============================================================
# Revenue Distribution
# ============================================================

def _render_distribution(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Revenue Distribution & Volatility",
        (
            "Distribution of daily revenue and "
            "short-term percentage movement."
        ),
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.histogram(
            daily,
            x="Revenue",
            nbins=40,
            title=(
                "Daily Revenue Distribution"
            ),
            color_discrete_sequence=[
                COLORS[
                    "uae_green"
                ]
            ],
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )

    with right:
        changes = (
            daily[
                "DailyRevenueChangePct"
            ]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .dropna()
        )

        change_frame = (
            pd.DataFrame(
                {
                    "DailyChangePct":
                        changes
                }
            )
        )

        figure = px.histogram(
            change_frame,
            x="DailyChangePct",
            nbins=50,
            title=(
                "Daily Revenue Change "
                "Distribution"
            ),
            color_discrete_sequence=[
                COLORS["gold"]
            ],
        )

        figure.add_vline(
            x=0,
            line_dash="dot",
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )


# ============================================================
# Correlation
# ============================================================

def _render_correlation(
    daily: pd.DataFrame,
) -> None:
    section_header(
        "Commercial Correlation Matrix",
        (
            "Descriptive relationships between "
            "daily commercial metrics. Correlation "
            "does not imply causation."
        ),
    )

    columns = [
        "Revenue",
        "GrossProfit",
        "Orders",
        "Customers",
        "GrossUnits",
        "ReturnedUnits",
        "NetUnits",
        "AOV",
        "GrossMarginPct",
        "ReturnRatePct",
    ]

    available = [
        column
        for column in columns
        if column in daily.columns
    ]

    correlation = (
        daily[
            available
        ]
        .corr()
    )

    figure = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        zmin=-1,
        zmax=1,
        color_continuous_scale=(
            "RdBu_r"
        ),
        title=(
            "Daily KPI Correlation"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            580,
        ),
        use_container_width=True,
    )


# ============================================================
# Top / Bottom Months
# ============================================================

def _render_month_ranking(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Best & Weakest Trading Months",
        (
            "Ranking by filtered monthly revenue "
            "with margin context."
        ),
    )

    count = min(
        10,
        len(monthly),
    )

    top = (
        monthly.nlargest(
            count,
            "Revenue",
        )
        .copy()
    )

    bottom = (
        monthly.nsmallest(
            count,
            "Revenue",
        )
        .copy()
    )

    top[
        "MonthLabel"
    ] = top[
        "MonthStart"
    ].dt.strftime(
        "%b %Y"
    )

    bottom[
        "MonthLabel"
    ] = bottom[
        "MonthStart"
    ].dt.strftime(
        "%b %Y"
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.bar(
            top.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="MonthLabel",
            orientation="h",
            color="GrossMarginPct",
            title="Top Revenue Months",
            color_continuous_scale=(
                "YlGn"
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
        figure = px.bar(
            bottom.sort_values(
                "Revenue",
                ascending=False,
            ),
            x="Revenue",
            y="MonthLabel",
            orientation="h",
            color="GrossMarginPct",
            title="Lowest Revenue Months",
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                470,
            ),
            use_container_width=True,
        )


# ============================================================
# Data Explorer
# ============================================================

def _render_data_explorer(
    user,
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Sales Data Explorer",
        (
            "Filtered analytical datasets "
            "used throughout this dashboard."
        ),
    )

    monthly_tab, daily_tab = (
        st.tabs(
            [
                "Monthly Performance",
                "Daily Performance",
            ]
        )
    )

    with monthly_tab:
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
                "monthly sales"
            ),
            file_name=(
                "sales_monthly_filtered.csv"
            ),
            key=(
                "sales_export_monthly"
            ),
        )

    with daily_tab:
        export_daily = daily[
            [
                column
                for column in [
                    "FullDate",
                    "Orders",
                    "Customers",
                    "GrossUnits",
                    "ReturnedUnits",
                    "NetUnits",
                    "Revenue",
                    "GrossProfit",
                    "AOV",
                    "GrossMarginPct",
                    "ReturnRatePct",
                ]
                if column
                in daily.columns
            ]
        ].copy()

        st.dataframe(
            export_daily,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=export_daily,
            label=(
                "Export filtered "
                "daily sales"
            ),
            file_name=(
                "sales_daily_filtered.csv"
            ),
            key=(
                "sales_export_daily"
            ),
        )


# ============================================================
# Main Render
# ============================================================

def render(
    user,
    filters,
) -> None:
    page_header(
        "Sales & Growth Intelligence",
        (
            "Advanced commercial analytics covering "
            "revenue, profit, MoM, YoY, rolling trends, "
            "seasonality, trading-week behavior, "
            "volatility and anomaly screening."
        ),
        "UAE COMMERCIAL PERFORMANCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

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

    if (
        monthly.empty
        or daily.empty
    ):
        st.warning(
            "No sales data matches "
            "the active analytical filters."
        )

        return

    monthly = (
        _prepare_monthly(
            monthly
        )
    )

    daily = (
        _prepare_daily(
            daily
        )
    )

    _render_kpis(
        summary,
        monthly,
    )

    _render_monthly_trends(
        monthly
    )

    _render_growth(
        monthly
    )

    _render_daily_trend(
        daily
    )

    _render_weekday_analysis(
        daily
    )

    _render_seasonality(
        daily
    )

    _render_annual_performance(
        daily
    )

    _render_anomaly_analysis(
        daily
    )

    _render_distribution(
        daily
    )

    _render_correlation(
        daily
    )

    _render_month_ranking(
        monthly
    )

    _render_data_explorer(
        user,
        daily,
        monthly,
    )