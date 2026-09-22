from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components import (
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
from src.analytics.target_data import (
    add_target_performance_score,
    get_filtered_annual_targets,
    get_filtered_emirate_targets,
    get_filtered_monthly_targets,
    get_filtered_store_month_targets,
    get_filtered_store_targets,
    get_filtered_target_performance,
    get_filtered_target_summary,
    get_target_achievement_distribution,
    get_target_underperformers,
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


def _achievement_color(
    value,
) -> str:
    numeric = _safe_float(
        value
    )

    if numeric >= 100:
        return COLORS[
            "uae_green"
        ]

    if numeric >= 90:
        return COLORS[
            "gold"
        ]

    return COLORS[
        "uae_red"
    ]


def _variance_tone(
    value,
) -> str:
    numeric = _safe_float(
        value
    )

    if numeric > 0:
        return "green"

    if numeric < 0:
        return "red"

    return "gold"


def _achievement_band(
    value,
) -> str:
    numeric = _safe_float(
        value
    )

    if numeric >= 110:
        return "110%+"

    if numeric >= 100:
        return "100-110%"

    if numeric >= 90:
        return "90-100%"

    if numeric >= 80:
        return "80-90%"

    return "<80%"


# ============================================================
# KPI Section
# ============================================================

def _render_kpis(
    summary: dict,
) -> None:
    section_header(
        "Enterprise Target KPI Pulse",
        (
            "Actual performance versus plan "
            "inside the current RLS and analytical scope."
        ),
    )

    revenue_achievement = (
        _safe_float(
            summary[
                "RevenueAchievementPct"
            ]
        )
    )

    profit_achievement = (
        _safe_float(
            summary[
                "ProfitAchievementPct"
            ]
        )
    )

    orders_achievement = (
        _safe_float(
            summary[
                "OrdersAchievementPct"
            ]
        )
    )

    row = st.columns(4)

    metric(
        row[0],
        "Actual Revenue",
        money(
            summary[
                "ActualRevenue"
            ]
        ),
    )

    metric(
        row[1],
        "Revenue Target",
        money(
            summary[
                "RevenueTarget"
            ]
        ),
    )

    metric(
        row[2],
        "Revenue Achievement",
        percentage(
            revenue_achievement
        ),
        revenue_achievement - 100,
    )

    metric(
        row[3],
        "Revenue Variance",
        money(
            summary[
                "RevenueVariance"
            ]
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Actual Gross Profit",
        money(
            summary[
                "ActualGrossProfit"
            ]
        ),
    )

    metric(
        row[1],
        "Profit Target",
        money(
            summary[
                "GrossProfitTarget"
            ]
        ),
    )

    metric(
        row[2],
        "Profit Achievement",
        percentage(
            profit_achievement
        ),
        profit_achievement - 100,
    )

    metric(
        row[3],
        "Profit Variance",
        money(
            summary[
                "ProfitVariance"
            ]
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Actual Orders",
        number(
            summary[
                "ActualOrders"
            ]
        ),
    )

    metric(
        row[1],
        "Orders Target",
        number(
            summary[
                "OrdersTarget"
            ]
        ),
    )

    metric(
        row[2],
        "Orders Achievement",
        percentage(
            orders_achievement
        ),
        orders_achievement - 100,
    )

    metric(
        row[3],
        "Orders Variance",
        number(
            summary[
                "OrdersVariance"
            ]
        ),
    )


# ============================================================
# Executive Signals
# ============================================================

def _render_signals(
    summary: dict,
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Performance Management Signals",
        (
            "Immediate indicators for target "
            "attainment and intervention."
        ),
    )

    revenue_variance = (
        _safe_float(
            summary[
                "RevenueVariance"
            ]
        )
    )

    profit_variance = (
        _safe_float(
            summary[
                "ProfitVariance"
            ]
        )
    )

    if stores.empty:
        best_store = None
        weakest_store = None

    else:
        best_store = (
            stores.sort_values(
                "RevenueAchievementPct",
                ascending=False,
            )
            .iloc[0]
        )

        weakest_store = (
            stores.sort_values(
                "RevenueAchievementPct",
                ascending=True,
            )
            .iloc[0]
        )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "REVENUE VARIANCE",
            money(
                revenue_variance
            ),
            (
                "Actual revenue minus "
                "planned revenue."
            ),
            _variance_tone(
                revenue_variance
            ),
        )

    with columns[1]:
        insight_card(
            "PROFIT VARIANCE",
            money(
                profit_variance
            ),
            (
                "Actual gross profit minus "
                "planned gross profit."
            ),
            _variance_tone(
                profit_variance
            ),
        )

    with columns[2]:
        if best_store is None:
            insight_card(
                "TOP STORE",
                "N/A",
                "No store data.",
                "gold",
            )

        else:
            insight_card(
                "TOP STORE",
                str(
                    best_store[
                        "StoreCode"
                    ]
                ),
                percentage(
                    best_store[
                        "RevenueAchievementPct"
                    ]
                ),
                "green",
            )

    with columns[3]:
        if weakest_store is None:
            insight_card(
                "ATTENTION STORE",
                "N/A",
                "No store data.",
                "gold",
            )

        else:
            insight_card(
                "ATTENTION STORE",
                str(
                    weakest_store[
                        "StoreCode"
                    ]
                ),
                percentage(
                    weakest_store[
                        "RevenueAchievementPct"
                    ]
                ),
                (
                    "red"
                    if _safe_float(
                        weakest_store[
                            "RevenueAchievementPct"
                        ]
                    )
                    < 90
                    else "gold"
                ),
            )


# ============================================================
# Achievement Gauges
# ============================================================

def _render_gauges(
    summary: dict,
) -> None:
    section_header(
        "Target Achievement Gauges",
        (
            "Revenue, gross profit and "
            "order attainment against plan."
        ),
    )

    metrics = [
        (
            "Revenue",
            summary[
                "RevenueAchievementPct"
            ],
        ),
        (
            "Gross Profit",
            summary[
                "ProfitAchievementPct"
            ],
        ),
        (
            "Orders",
            summary[
                "OrdersAchievementPct"
            ],
        ),
    ]

    columns = st.columns(3)

    for (
        container,
        (
            title,
            value,
        ),
    ) in zip(
        columns,
        metrics,
    ):
        achievement = (
            _safe_float(
                value
            )
        )

        figure = go.Figure(
            go.Indicator(
                mode=(
                    "gauge+number"
                ),

                value=achievement,

                number={
                    "suffix": "%",
                    "font": {
                        "color":
                            COLORS[
                                "text"
                            ]
                    },
                },

                title={
                    "text": title,
                    "font": {
                        "color":
                            COLORS[
                                "muted"
                            ]
                    },
                },

                gauge={
                    "axis": {
                        "range":
                            [
                                0,
                                max(
                                    120,
                                    achievement
                                    * 1.05,
                                ),
                            ]
                    },

                    "bar": {
                        "color":
                            _achievement_color(
                                achievement
                            )
                    },

                    "bgcolor":
                        COLORS[
                            "surface"
                        ],

                    "bordercolor":
                        COLORS[
                            "border"
                        ],

                    "steps": [
                        {
                            "range":
                                [
                                    0,
                                    80,
                                ],

                            "color":
                                "rgba(206,17,38,.14)",
                        },
                        {
                            "range":
                                [
                                    80,
                                    100,
                                ],

                            "color":
                                "rgba(214,179,74,.14)",
                        },
                        {
                            "range":
                                [
                                    100,
                                    max(
                                        120,
                                        achievement
                                        * 1.05,
                                    ),
                                ],

                            "color":
                                "rgba(0,132,61,.14)",
                        },
                    ],

                    "threshold": {
                        "line": {
                            "color":
                                COLORS[
                                    "gold"
                                ],
                            "width":
                                3,
                        },

                        "value":
                            100,
                    },
                },
            )
        )

        with container:
            st.plotly_chart(
                style_figure(
                    figure,
                    310,
                    legend=False,
                ),
                use_container_width=True,
            )


# ============================================================
# Monthly Trend
# ============================================================

def _render_monthly_trend(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Monthly Plan Execution",
        (
            "Actual versus target trajectory "
            "and monthly variance."
        ),
    )

    if monthly.empty:
        return

    left, right = st.columns(
        [1.5, 1]
    )

    with left:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "ActualRevenue"
                ],
                name="Actual Revenue",
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
                    "RevenueTarget"
                ],
                name="Revenue Target",
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=2.5,
                    dash="dash",
                ),
            )
        )

        figure.update_layout(
            title=(
                "Actual Revenue vs Target"
            ),
            xaxis_title=None,
            yaxis_title="AED",
        )

        st.plotly_chart(
            style_figure(
                figure,
                460,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            monthly,
            x="MonthStart",
            y=(
                "RevenueAchievementPct"
            ),
            color=(
                "RevenueAchievementPct"
            ),
            title=(
                "Monthly Revenue Achievement"
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
            color_continuous_midpoint=100,
        )

        figure.add_hline(
            y=100,
            line_dash="dash",
            line_color=(
                COLORS["gold"]
            ),
        )

        figure.update_layout(
            coloraxis_showscale=False,
            yaxis_title=(
                "Achievement %"
            ),
            xaxis_title=None,
        )

        st.plotly_chart(
            style_figure(
                figure,
                460,
            ),
            use_container_width=True,
        )

    left, right = st.columns(2)

    with left:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=monthly[
                    "MonthStart"
                ],
                y=monthly[
                    "ActualGrossProfit"
                ],
                name="Actual Profit",
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
                    "GrossProfitTarget"
                ],
                name="Profit Target",
                mode="lines",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=2.5,
                    dash="dash",
                ),
            )
        )

        figure.update_layout(
            title=(
                "Gross Profit Actual vs Target"
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
                    "ActualOrders"
                ],
                name="Actual Orders",
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "info"
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
                    "OrdersTarget"
                ],
                name="Orders Target",
                mode="lines",
                line=dict(
                    color=COLORS[
                        "gold"
                    ],
                    width=2.5,
                    dash="dash",
                ),
            )
        )

        figure.update_layout(
            title=(
                "Orders Actual vs Target"
            ),
            xaxis_title=None,
            yaxis_title="Orders",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )


# ============================================================
# Variance Analysis
# ============================================================

def _render_variance_analysis(
    monthly: pd.DataFrame,
) -> None:
    section_header(
        "Monthly Variance Intelligence",
        (
            "Magnitude and direction of "
            "monthly plan variance."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            monthly,
            x="MonthStart",
            y="RevenueVariance",
            color="RevenueVariance",
            title=(
                "Revenue Variance to Plan"
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
            yaxis_title="AED",
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            monthly,
            x="MonthStart",
            y="ProfitVariance",
            color="ProfitVariance",
            title=(
                "Gross Profit Variance to Plan"
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
            yaxis_title="AED",
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )


# ============================================================
# Annual Performance
# ============================================================

def _render_annual_performance(
    annual: pd.DataFrame,
) -> None:
    if annual.empty:
        return

    section_header(
        "Annual Target Performance",
        (
            "Year-level plan attainment across "
            "revenue, profit and orders."
        ),
    )

    display = annual.copy()

    display[
        "Year"
    ] = (
        display[
            "TargetYear"
        ]
        .astype(str)
    )

    long = (
        display[
            [
                "Year",
                "RevenueAchievementPct",
                "ProfitAchievementPct",
                "OrdersAchievementPct",
            ]
        ]
        .melt(
            id_vars=[
                "Year"
            ],
            var_name="Metric",
            value_name=(
                "AchievementPct"
            ),
        )
    )

    figure = px.bar(
        long,
        x="Year",
        y="AchievementPct",
        color="Metric",
        barmode="group",
        title=(
            "Annual Achievement by KPI"
        ),
        color_discrete_map={
            "RevenueAchievementPct":
                COLORS[
                    "uae_green"
                ],
            "ProfitAchievementPct":
                COLORS["gold"],
            "OrdersAchievementPct":
                COLORS["info"],
        },
    )

    figure.add_hline(
        y=100,
        line_dash="dash",
    )

    figure.update_layout(
        yaxis_title="Achievement %",
        xaxis_title=None,
    )

    st.plotly_chart(
        style_figure(
            figure,
            440,
        ),
        use_container_width=True,
    )


# ============================================================
# Emirate Performance
# ============================================================

def _render_emirate_performance(
    emirates: pd.DataFrame,
) -> None:
    if emirates.empty:
        return

    section_header(
        "Emirate Target Performance",
        (
            "Commercial target execution "
            "across visible UAE emirates."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            emirates.sort_values(
                "RevenueAchievementPct"
            ),
            x=(
                "RevenueAchievementPct"
            ),
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "Stores",
                "ActualRevenue",
                "RevenueTarget",
                "RevenueVariance",
                "ProfitAchievementPct",
                "OrdersAchievementPct",
            ],
            title=(
                "Revenue Achievement by Emirate"
            ),
        )

        figure.add_vline(
            x=100,
            line_dash="dash",
        )

        figure.update_layout(
            showlegend=False,
            xaxis_title=(
                "Achievement %"
            ),
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
            emirates,
            x=(
                "RevenueAchievementPct"
            ),
            y=(
                "ProfitAchievementPct"
            ),
            size="ActualRevenue",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_name="EmirateName",
            hover_data=[
                "OrdersAchievementPct",
                "RevenueVariance",
                "ProfitVariance",
            ],
            title=(
                "Emirate Revenue / "
                "Profit Achievement"
            ),
        )

        figure.add_vline(
            x=100,
            line_dash="dash",
        )

        figure.add_hline(
            y=100,
            line_dash="dash",
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )


# ============================================================
# Store Ranking
# ============================================================

def _render_store_ranking(
    stores: pd.DataFrame,
) -> None:
    if stores.empty:
        return

    section_header(
        "Store Target Ranking",
        (
            "Store-level target achievement "
            "and commercial variance."
        ),
    )

    count = min(
        20,
        len(stores),
    )

    left, right = st.columns(2)

    with left:
        top = (
            stores.nlargest(
                count,
                "RevenueAchievementPct",
            )
            .sort_values(
                "RevenueAchievementPct"
            )
        )

        figure = px.bar(
            top,
            x=(
                "RevenueAchievementPct"
            ),
            y="StoreCode",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "StoreName",
                "ActualRevenue",
                "RevenueTarget",
                "RevenueVariance",
                "ProfitAchievementPct",
                "PerformanceScore",
            ],
            title=(
                "Highest Revenue Achievement"
            ),
        )

        figure.add_vline(
            x=100,
            line_dash="dash",
        )

        st.plotly_chart(
            style_figure(
                figure,
                540,
            ),
            use_container_width=True,
        )

    with right:
        bottom = (
            stores.nsmallest(
                count,
                "RevenueAchievementPct",
            )
            .sort_values(
                "RevenueAchievementPct",
                ascending=False,
            )
        )

        figure = px.bar(
            bottom,
            x=(
                "RevenueAchievementPct"
            ),
            y="StoreCode",
            orientation="h",
            color=(
                "RevenueAchievementPct"
            ),
            hover_data=[
                "StoreName",
                "EmirateName",
                "RevenueVariance",
                "ProfitAchievementPct",
                "TargetStatus",
            ],
            title=(
                "Lowest Revenue Achievement"
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
            color_continuous_midpoint=100,
        )

        figure.add_vline(
            x=100,
            line_dash="dash",
        )

        figure.update_layout(
            coloraxis_showscale=False,
        )

        st.plotly_chart(
            style_figure(
                figure,
                540,
            ),
            use_container_width=True,
        )


# ============================================================
# Store Performance Matrix
# ============================================================

def _render_store_matrix(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Store Achievement Matrix",
        (
            "Revenue, profit and order execution "
            "in a single performance view."
        ),
    )

    figure = px.scatter(
        stores,
        x=(
            "RevenueAchievementPct"
        ),
        y=(
            "ProfitAchievementPct"
        ),
        size="ActualRevenue",
        color="PerformanceTier",
        hover_name="StoreName",
        hover_data=[
            "StoreCode",
            "EmirateName",
            "OrdersAchievementPct",
            "RevenueVariance",
            "ProfitVariance",
            "PerformanceScore",
            "TargetStatus",
        ],
        title=(
            "Revenue / Profit "
            "Achievement Matrix"
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

    figure.add_vline(
        x=100,
        line_dash="dash",
        line_color=(
            COLORS["muted"]
        ),
    )

    figure.add_hline(
        y=100,
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

    figure = px.scatter(
        stores,
        x=(
            "RevenueAchievementPct"
        ),
        y=(
            "OrdersAchievementPct"
        ),
        size="ActualOrders",
        color="EmirateName",
        color_discrete_map=(
            EMIRATE_COLORS
        ),
        hover_name="StoreName",
        hover_data=[
            "StoreCode",
            "ProfitAchievementPct",
            "PerformanceScore",
        ],
        title=(
            "Revenue / Orders "
            "Achievement Matrix"
        ),
    )

    figure.add_vline(
        x=100,
        line_dash="dash",
    )

    figure.add_hline(
        y=100,
        line_dash="dash",
    )

    st.plotly_chart(
        style_figure(
            figure,
            480,
        ),
        use_container_width=True,
    )


# ============================================================
# Achievement Distribution
# ============================================================

def _render_distribution(
    distribution: pd.DataFrame,
) -> None:
    if distribution.empty:
        return

    section_header(
        "Target Achievement Distribution",
        (
            "Store population by revenue "
            "achievement band."
        ),
    )

    order = [
        "<80%",
        "80-90%",
        "90-100%",
        "100-110%",
        "110%+",
    ]

    figure = px.bar(
        distribution,
        x="AchievementBand",
        y="Stores",
        color="AchievementBand",
        text="Stores",
        hover_data=[
            "ActualRevenue",
            "RevenueTarget",
            "RevenueVariance",
        ],
        category_orders={
            "AchievementBand":
                order
        },
        title=(
            "Stores by Revenue "
            "Achievement Band"
        ),
        color_discrete_map={
            "<80%":
                COLORS[
                    "uae_red"
                ],
            "80-90%":
                "#E88A32",
            "90-100%":
                COLORS["gold"],
            "100-110%":
                COLORS["info"],
            "110%+":
                COLORS[
                    "uae_green"
                ],
        },
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
# Performance Score
# ============================================================

def _render_performance_score(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Composite Target Performance Score",
        (
            "Relative management score combining "
            "revenue, profit and order attainment."
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
            "RevenueAchievementPct",
            "ProfitAchievementPct",
            "OrdersAchievementPct",
            "TargetStatus",
        ],
        title=(
            "Store Target Performance Score"
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
                500,
                len(stores)
                * 25,
            ),
        ),
        use_container_width=True,
    )

    st.caption(
        "Performance Score weights: Revenue Achievement 45%, "
        "Profit Achievement 35%, Orders Achievement 20%. "
        "It is a management prioritization score, not an "
        "official accounting KPI."
    )


# ============================================================
# Store x Month Heatmap
# ============================================================

def _render_heatmap(
    store_month: pd.DataFrame,
) -> None:
    if store_month.empty:
        return

    section_header(
        "Store x Month Achievement Heatmap",
        (
            "Identify persistent performance gaps "
            "and sustained overachievement."
        ),
    )

    data = store_month.copy()

    data[
        "MonthLabel"
    ] = (
        data[
            "MonthStart"
        ]
        .dt.strftime(
            "%Y-%m"
        )
    )

    matrix = (
        data.pivot_table(
            index="StoreCode",
            columns="MonthLabel",
            values=(
                "RevenueAchievementPct"
            ),
            aggfunc="mean",
        )
    )

    figure = px.imshow(
        matrix,
        aspect="auto",
        text_auto=".0f",
        color_continuous_scale=[
            [
                0.0,
                COLORS[
                    "uae_red"
                ],
            ],
            [
                .5,
                COLORS[
                    "gold"
                ],
            ],
            [
                1.0,
                COLORS[
                    "uae_green"
                ],
            ],
        ],
        zmin=75,
        zmax=125,
        labels={
            "x":
                "Month",
            "y":
                "Store",
            "color":
                "Achievement %",
        },
        title=(
            "Revenue Achievement Heatmap"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                500,
                len(matrix)
                * 27,
            ),
        ),
        use_container_width=True,
    )


# ============================================================
# Underperformance
# ============================================================

def _render_underperformers(
    underperformers: pd.DataFrame,
) -> None:
    section_header(
        "Underperformance Watchlist",
        (
            "Stores below 90% aggregate "
            "revenue target achievement."
        ),
    )

    if underperformers.empty:
        st.success(
            "No stores are below the "
            "90% revenue achievement threshold."
        )
        return

    total_gap = _safe_float(
        underperformers[
            "RevenueVariance"
        ].sum()
    )

    row = st.columns(3)

    metric(
        row[0],
        "Stores Below 90%",
        number(
            len(
                underperformers
            )
        ),
    )

    metric(
        row[1],
        "Combined Revenue Gap",
        money(
            total_gap
        ),
    )

    metric(
        row[2],
        "Lowest Achievement",
        percentage(
            underperformers[
                "RevenueAchievementPct"
            ].min()
        ),
    )

    figure = px.bar(
        underperformers.sort_values(
            "RevenueAchievementPct"
        ),
        x=(
            "RevenueAchievementPct"
        ),
        y="StoreCode",
        orientation="h",
        color="RevenueVariance",
        hover_data=[
            "StoreName",
            "EmirateName",
            "ActualRevenue",
            "RevenueTarget",
            "ProfitAchievementPct",
            "OrdersAchievementPct",
        ],
        title=(
            "Stores Below 90% Revenue Target"
        ),
        color_continuous_scale=(
            "Reds"
        ),
    )

    figure.add_vline(
        x=90,
        line_dash="dash",
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                420,
                len(
                    underperformers
                )
                * 28,
            ),
        ),
        use_container_width=True,
    )


# ============================================================
# Management Action Queue
# ============================================================

def _render_action_queue(
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Performance Management Action Queue",
        (
            "Stores grouped by multi-KPI "
            "target execution status."
        ),
    )

    status_summary = (
        stores.groupby(
            "TargetStatus",
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
            AvgPerformanceScore=(
                "PerformanceScore",
                "mean",
            ),
        )
    )

    figure = px.bar(
        status_summary.sort_values(
            "ActualRevenue"
        ),
        x="ActualRevenue",
        y="TargetStatus",
        orientation="h",
        color="TargetStatus",
        text="Stores",
        hover_data=[
            "RevenueTarget",
            "RevenueVariance",
            "AvgPerformanceScore",
        ],
        title=(
            "Revenue by Target Status"
        ),
        color_discrete_map={
            "All Targets Achieved":
                COLORS[
                    "uae_green"
                ],
            "Revenue Achieved / Profit Gap":
                COLORS[
                    "gold"
                ],
            "Material Underperformance":
                COLORS[
                    "uae_red"
                ],
            "Near Target":
                COLORS["info"],
            "Mixed Performance":
                COLORS[
                    "muted"
                ],
        },
    )

    figure.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        style_figure(
            figure,
            430,
            legend=False,
        ),
        use_container_width=True,
    )

    attention = (
        stores[
            stores[
                "TargetStatus"
            ]
            != (
                "All Targets Achieved"
            )
        ]
        .sort_values(
            [
                "PerformanceScore",
                "RevenueAchievementPct",
            ],
            ascending=[
                True,
                True,
            ],
        )
        .copy()
    )

    if not attention.empty:
        st.dataframe(
            attention[
                [
                    "StoreCode",
                    "StoreName",
                    "EmirateName",
                    "ActualRevenue",
                    "RevenueTarget",
                    "RevenueVariance",
                    "RevenueAchievementPct",
                    "ProfitAchievementPct",
                    "OrdersAchievementPct",
                    "PerformanceScore",
                    "PerformanceTier",
                    "TargetStatus",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Data Explorer & Exports
# ============================================================

def _render_data_explorer(
    user,
    detail: pd.DataFrame,
    monthly: pd.DataFrame,
    stores: pd.DataFrame,
    emirates: pd.DataFrame,
    annual: pd.DataFrame,
) -> None:
    section_header(
        "Target Performance Data Explorer",
        (
            "Secure filtered planning datasets "
            "available for review and export."
        ),
    )

    (
        store_tab,
        month_tab,
        emirate_tab,
        annual_tab,
        detail_tab,
    ) = st.tabs(
        [
            "Stores",
            "Monthly",
            "Emirates",
            "Annual",
            "Detail",
        ]
    )

    with store_tab:
        st.dataframe(
            stores,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=stores,
            label=(
                "Export store target performance"
            ),
            file_name=(
                "targets_store_performance.csv"
            ),
            key=(
                "targets_export_stores"
            ),
        )

    with month_tab:
        st.dataframe(
            monthly,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=monthly,
            label=(
                "Export monthly target performance"
            ),
            file_name=(
                "targets_monthly_performance.csv"
            ),
            key=(
                "targets_export_monthly"
            ),
        )

    with emirate_tab:
        st.dataframe(
            emirates,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=emirates,
            label=(
                "Export emirate target performance"
            ),
            file_name=(
                "targets_emirate_performance.csv"
            ),
            key=(
                "targets_export_emirates"
            ),
        )

    with annual_tab:
        st.dataframe(
            annual,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=annual,
            label=(
                "Export annual target performance"
            ),
            file_name=(
                "targets_annual_performance.csv"
            ),
            key=(
                "targets_export_annual"
            ),
        )

    with detail_tab:
        st.dataframe(
            detail,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=detail,
            label=(
                "Export target detail"
            ),
            file_name=(
                "targets_filtered_detail.csv"
            ),
            key=(
                "targets_export_detail"
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
        "Targets & Achievement Command Center",
        (
            "Advanced performance-management intelligence "
            "covering revenue, gross profit and order targets, "
            "monthly variance, store and emirate rankings, "
            "underperformance and management action signals."
        ),
        "UAE PERFORMANCE MANAGEMENT",
    )

    st.caption(
        "Target reporting period: "
        f"{_period_label(filters)}"
    )

    if (
        filters.start_date
        is not None
        or filters.end_date
        is not None
    ):
        st.info(
            "Targets are monthly. Date filters are applied "
            "at target-month level: any selected date inside "
            "a month includes that month's target."
        )

    summary = (
        get_filtered_target_summary(
            user,
            filters,
        )
    )

    detail = (
        get_filtered_target_performance(
            user,
            filters,
        )
    )

    if (
        detail.empty
        or _safe_float(
            summary[
                "RevenueTarget"
            ]
        )
        == 0
    ):
        st.warning(
            "No target records match "
            "the active analytical filters."
        )
        return

    monthly = (
        get_filtered_monthly_targets(
            user,
            filters,
        )
    )

    stores = (
        get_filtered_store_targets(
            user,
            filters,
        )
    )

    emirates = (
        get_filtered_emirate_targets(
            user,
            filters,
        )
    )

    annual = (
        get_filtered_annual_targets(
            user,
            filters,
        )
    )

    store_month = (
        get_filtered_store_month_targets(
            user,
            filters,
        )
    )

    distribution = (
        get_target_achievement_distribution(
            user,
            filters,
        )
    )

    underperformers = (
        get_target_underperformers(
            user,
            filters,
            threshold_pct=90,
        )
    )

    stores = (
        add_target_performance_score(
            stores
        )
    )

    _render_kpis(
        summary
    )

    _render_signals(
        summary,
        stores,
    )

    _render_gauges(
        summary
    )

    _render_monthly_trend(
        monthly
    )

    _render_variance_analysis(
        monthly
    )

    _render_annual_performance(
        annual
    )

    _render_emirate_performance(
        emirates
    )

    _render_store_ranking(
        stores
    )

    _render_store_matrix(
        stores
    )

    _render_distribution(
        distribution
    )

    _render_performance_score(
        stores
    )

    _render_heatmap(
        store_month
    )

    _render_underperformers(
        underperformers
    )

    _render_action_queue(
        stores
    )

    _render_data_explorer(
        user,
        detail,
        monthly,
        stores,
        emirates,
        annual,
    )