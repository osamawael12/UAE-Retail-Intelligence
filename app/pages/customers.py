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
    RFM_COLORS,
)
from src.analytics.customer_data import (
    get_filtered_cohort_retention,
    get_filtered_cohort_revenue,
    get_filtered_customer_concentration,
    get_filtered_customer_lifecycle,
    get_filtered_customer_metrics,
    get_filtered_customer_rfm,
    get_filtered_customer_summary,
    get_filtered_frequency_distribution,
    get_filtered_monthly_customer_activity,
    get_filtered_rfm_summary,
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

    minimum = _safe_float(
        values.min()
    )

    maximum = _safe_float(
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


def _prepare_customer_value(
    rfm: pd.DataFrame,
) -> pd.DataFrame:
    data = rfm.copy()

    if data.empty:
        return data

    monetary_score = (
        _min_max_score(
            data["Monetary"]
        )
    )

    frequency_score = (
        _min_max_score(
            data["Frequency"]
        )
    )

    profit_score = (
        _min_max_score(
            data["GrossProfit"]
        )
    )

    recency_score = (
        _min_max_score(
            data["Recency"],
            reverse=True,
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
        "CustomerValueScore"
    ] = (
        monetary_score
        * .35
        + frequency_score
        * .25
        + profit_score
        * .20
        + recency_score
        * .15
        + return_health_score
        * .05
    )

    data[
        "CustomerValueScore"
    ] = (
        data[
            "CustomerValueScore"
        ]
        .clip(
            0,
            100,
        )
    )

    data[
        "ValueClass"
    ] = pd.cut(
        data[
            "CustomerValueScore"
        ],
        bins=[
            -np.inf,
            40,
            60,
            80,
            np.inf,
        ],
        labels=[
            "Low",
            "Developing",
            "High",
            "Elite",
        ],
    )

    data[
        "ActionFlag"
    ] = np.select(
        [
            (
                data[
                    "Segment"
                ]
                == "At Risk"
            )
            & (
                data[
                    "MScore"
                ]
                >= 4
            ),

            (
                data[
                    "Segment"
                ]
                == "Champions"
            ),

            (
                data[
                    "Segment"
                ]
                == "Promising"
            ),

            (
                data[
                    "Segment"
                ]
                == "Hibernating"
            )
            & (
                data[
                    "MScore"
                ]
                >= 3
            ),

            (
                data[
                    "ReturnRatePct"
                ]
                >= data[
                    "ReturnRatePct"
                ].quantile(
                    .90
                )
            ),
        ],
        [
            "High-Value Win-Back",
            "VIP / Retain",
            "Nurture",
            "Reactivation",
            "Return Risk Review",
        ],
        default="Standard",
    )

    return data


# ============================================================
# KPI Section
# ============================================================

def _render_kpis(
    summary: dict,
    rfm: pd.DataFrame,
) -> None:
    section_header(
        "Customer KPI Pulse",
        (
            "Behavioral customer performance "
            "inside the active RLS and filter scope."
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Active Customers",
        number(
            summary[
                "Customers"
            ]
        ),
    )

    metric(
        row[1],
        "Customer Revenue",
        money(
            summary[
                "Revenue"
            ]
        ),
    )

    metric(
        row[2],
        "Revenue / Customer",
        money(
            summary[
                "RevenuePerCustomer"
            ]
        ),
    )

    metric(
        row[3],
        "Average Order Value",
        money(
            summary["AOV"]
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Repeat Customers",
        number(
            summary[
                "RepeatCustomers"
            ]
        ),
    )

    metric(
        row[1],
        "Repeat Customer Rate",
        percentage(
            summary[
                "RepeatCustomerPct"
            ]
        ),
    )

    metric(
        row[2],
        "Orders / Customer",
        f"{_safe_float(summary['OrdersPerCustomer']):.2f}",
    )

    metric(
        row[3],
        "Customer Return Rate",
        percentage(
            summary[
                "ReturnRatePct"
            ]
        ),
    )

    champions = int(
        rfm[
            "Segment"
        ]
        .eq("Champions")
        .sum()
    )

    at_risk = int(
        rfm[
            "Segment"
        ]
        .eq("At Risk")
        .sum()
    )

    hibernating = int(
        rfm[
            "Segment"
        ]
        .eq("Hibernating")
        .sum()
    )

    high_value = int(
        rfm[
            "ValueClass"
        ]
        .isin(
            [
                "High",
                "Elite",
            ]
        )
        .sum()
    )

    row = st.columns(4)

    metric(
        row[0],
        "Champions",
        number(champions),
    )

    metric(
        row[1],
        "At Risk",
        number(at_risk),
    )

    metric(
        row[2],
        "Hibernating",
        number(
            hibernating
        ),
    )

    metric(
        row[3],
        "High / Elite Value",
        number(
            high_value
        ),
    )


# ============================================================
# Customer Signals
# ============================================================

def _render_signals(
    rfm: pd.DataFrame,
    concentration: pd.DataFrame,
) -> None:
    section_header(
        "CRM Management Signals",
        (
            "High-value customer opportunities, "
            "retention exposure and revenue concentration."
        ),
    )

    highest_value = (
        rfm.sort_values(
            "Monetary",
            ascending=False,
        )
        .iloc[0]
    )

    winback = int(
        rfm[
            "ActionFlag"
        ]
        .eq(
            "High-Value Win-Back"
        )
        .sum()
    )

    vip = int(
        rfm[
            "ActionFlag"
        ]
        .eq("VIP / Retain")
        .sum()
    )

    top20_share = 0.0

    if not concentration.empty:
        top20 = (
            concentration[
                concentration[
                    "CustomerPct"
                ]
                <= 20
            ]
        )

        top20_share = (
            _safe_float(
                top20[
                    "Revenue"
                ].sum()
            )
            / _safe_float(
                concentration[
                    "Revenue"
                ].sum()
            )
            * 100
            if _safe_float(
                concentration[
                    "Revenue"
                ].sum()
            )
            else 0
        )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "TOP CUSTOMER VALUE",
            str(
                highest_value[
                    "CustomerCode"
                ]
            ),
            money(
                highest_value[
                    "Monetary"
                ]
            ),
            "green",
        )

    with columns[1]:
        insight_card(
            "VIP / RETAIN",
            number(vip),
            (
                "Champion customers "
                "for retention priority."
            ),
            "green",
        )

    with columns[2]:
        insight_card(
            "HIGH-VALUE WIN-BACK",
            number(winback),
            (
                "At-risk customers with "
                "high monetary value."
            ),
            "red",
        )

    with columns[3]:
        insight_card(
            "TOP 20% REVENUE SHARE",
            percentage(
                top20_share
            ),
            (
                "Revenue concentration among "
                "the highest-value customers."
            ),
            (
                "red"
                if top20_share >= 70
                else "gold"
                if top20_share >= 50
                else "green"
            ),
        )


# ============================================================
# RFM Overview
# ============================================================

def _render_rfm_overview(
    rfm: pd.DataFrame,
    segment_summary: pd.DataFrame,
) -> None:
    section_header(
        "RFM Segmentation",
        (
            "Recency, Frequency and Monetary scoring "
            "for customer prioritization."
        ),
    )

    left, right = st.columns(
        [1, 1.2]
    )

    with left:
        figure = px.treemap(
            segment_summary,
            path=[
                "Segment"
            ],
            values="Customers",
            color="Revenue",
            hover_data=[
                "RevenueSharePct",
                "AvgRecency",
                "AvgFrequency",
                "AvgMonetary",
            ],
            title=(
                "RFM Segment Population"
            ),
            color_continuous_scale=(
                "Viridis"
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
            rfm,
            x="Recency",
            y="Frequency",
            size="Monetary",
            color="Segment",
            hover_name=(
                "CustomerCode"
            ),
            hover_data=[
                "RFMScore",
                "AOV",
                "GrossProfit",
                "ReturnRatePct",
            ],
            title=(
                "Recency / Frequency / "
                "Monetary Matrix"
            ),
            color_discrete_map=(
                RFM_COLORS
            ),
            opacity=.68,
        )

        figure.update_layout(
            xaxis_title=(
                "Recency (Days)"
            ),
            yaxis_title=(
                "Purchase Frequency"
            ),
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
        figure = px.bar(
            segment_summary.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="Segment",
            orientation="h",
            color="Segment",
            color_discrete_map=(
                RFM_COLORS
            ),
            hover_data=[
                "Customers",
                "RevenueSharePct",
                "AvgAOV",
            ],
            title=(
                "Revenue by RFM Segment"
            ),
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

    with right:
        figure = px.scatter(
            segment_summary,
            x="AvgRecency",
            y="AvgFrequency",
            size="Customers",
            color="Segment",
            hover_name="Segment",
            hover_data=[
                "AvgMonetary",
                "RevenueSharePct",
            ],
            color_discrete_map=(
                RFM_COLORS
            ),
            title=(
                "Segment Behavioral Position"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )


# ============================================================
# RF Heatmaps
# ============================================================

def _render_rf_heatmap(
    rfm: pd.DataFrame,
) -> None:
    section_header(
        "RFM Score Heatmaps",
        (
            "Customer population and monetary "
            "value across Recency/Frequency cells."
        ),
    )

    rf = (
        rfm.groupby(
            [
                "RScore",
                "FScore",
            ],
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
            AvgMonetary=(
                "Monetary",
                "mean",
            ),
        )
    )

    customer_matrix = (
        rf.pivot(
            index="RScore",
            columns="FScore",
            values="Customers",
        )
        .fillna(0)
        .sort_index(
            ascending=False
        )
    )

    revenue_matrix = (
        rf.pivot(
            index="RScore",
            columns="FScore",
            values="Revenue",
        )
        .fillna(0)
        .sort_index(
            ascending=False
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.imshow(
            customer_matrix,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale=(
                "YlGn"
            ),
            labels={
                "x":
                    "Frequency Score",
                "y":
                    "Recency Score",
                "color":
                    "Customers",
            },
            title=(
                "RF Customer Count"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.imshow(
            revenue_matrix,
            text_auto=".3s",
            aspect="auto",
            color_continuous_scale=(
                "YlGnBu"
            ),
            labels={
                "x":
                    "Frequency Score",
                "y":
                    "Recency Score",
                "color":
                    "Revenue",
            },
            title=(
                "RF Revenue Matrix"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )


# ============================================================
# Customer Value
# ============================================================

def _render_customer_value(
    rfm: pd.DataFrame,
) -> None:
    section_header(
        "Customer Value Intelligence",
        (
            "Composite customer value based on monetary "
            "value, frequency, profit, recency and "
            "return health."
        ),
    )

    figure = px.scatter(
        rfm,
        x="Frequency",
        y="Monetary",
        size="CustomerValueScore",
        color="ValueClass",
        hover_name="CustomerCode",
        hover_data=[
            "Recency",
            "GrossProfit",
            "AOV",
            "Segment",
            "ActionFlag",
        ],
        title=(
            "Frequency / Monetary "
            "Customer Value Matrix"
        ),
        color_discrete_map={
            "Elite":
                COLORS[
                    "uae_green"
                ],
            "High":
                COLORS["info"],
            "Developing":
                COLORS["gold"],
            "Low":
                COLORS[
                    "uae_red"
                ],
        },
        opacity=.65,
    )

    st.plotly_chart(
        style_figure(
            figure,
            500,
        ),
        use_container_width=True,
    )

    value_summary = (
        rfm.groupby(
            "ValueClass",
            observed=False,
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
            AvgFrequency=(
                "Frequency",
                "mean",
            ),
            AvgRecency=(
                "Recency",
                "mean",
            ),
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            value_summary,
            x="ValueClass",
            y="Revenue",
            color="ValueClass",
            text="Customers",
            title=(
                "Revenue by Customer "
                "Value Class"
            ),
            color_discrete_map={
                "Elite":
                    COLORS[
                        "uae_green"
                    ],
                "High":
                    COLORS["info"],
                "Developing":
                    COLORS["gold"],
                "Low":
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
                legend=False,
            ),
            use_container_width=True,
        )

    with right:
        top = (
            rfm.nlargest(
                min(
                    20,
                    len(rfm),
                ),
                "CustomerValueScore",
            )
            .sort_values(
                "CustomerValueScore"
            )
        )

        figure = px.bar(
            top,
            x="CustomerValueScore",
            y="CustomerCode",
            orientation="h",
            color="Segment",
            color_discrete_map=(
                RFM_COLORS
            ),
            hover_data=[
                "Monetary",
                "Frequency",
                "Recency",
            ],
            title=(
                "Highest Customer Value Scores"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                520,
            ),
            use_container_width=True,
        )

    st.caption(
        "Customer Value Score is a relative "
        "CRM prioritization indicator, not a "
        "formal lifetime-value forecast."
    )


# ============================================================
# Revenue Concentration
# ============================================================

def _render_concentration(
    concentration: pd.DataFrame,
) -> None:
    if concentration.empty:
        return

    section_header(
        "Customer Revenue Concentration",
        (
            "Pareto analysis showing dependence "
            "on the highest-value customer base."
        ),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=concentration[
                "CustomerPct"
            ],
            y=concentration[
                "CumulativeRevenuePct"
            ],
            mode="lines",
            name=(
                "Cumulative Revenue"
            ),
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=3,
            ),
            fill="tozeroy",
            fillcolor=(
                "rgba(214,179,74,.08)"
            ),
        )
    )

    figure.add_hline(
        y=80,
        line_dash="dash",
        opacity=.5,
    )

    figure.add_vline(
        x=20,
        line_dash="dash",
        opacity=.5,
    )

    figure.update_layout(
        title=(
            "Customer Pareto Curve"
        ),
        xaxis_title=(
            "Cumulative Customers %"
        ),
        yaxis_title=(
            "Cumulative Revenue %"
        ),
        yaxis=dict(
            range=[
                0,
                105,
            ]
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            440,
        ),
        use_container_width=True,
    )

    shares = []

    for threshold in [
        1,
        5,
        10,
        20,
    ]:
        subset = (
            concentration[
                concentration[
                    "CustomerPct"
                ]
                <= threshold
            ]
        )

        share = (
            _safe_float(
                subset[
                    "Revenue"
                ].sum()
            )
            / _safe_float(
                concentration[
                    "Revenue"
                ].sum()
            )
            * 100
            if _safe_float(
                concentration[
                    "Revenue"
                ].sum()
            )
            else 0
        )

        shares.append(
            (
                threshold,
                share,
            )
        )

    columns = st.columns(4)

    for (
        container,
        (
            threshold,
            share,
        ),
    ) in zip(
        columns,
        shares,
    ):
        metric(
            container,
            (
                f"Top {threshold}% "
                "Revenue Share"
            ),
            percentage(
                share
            ),
        )


# ============================================================
# Frequency
# ============================================================

def _render_frequency(
    frequency: pd.DataFrame,
    lifecycle: pd.DataFrame,
) -> None:
    section_header(
        "Purchase Frequency & Lifecycle",
        (
            "One-time buyers, repeat customers "
            "and high-frequency relationships."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            frequency,
            x="FrequencyBand",
            y="Customers",
            color="Revenue",
            text="Customers",
            title=(
                "Customers by Order Frequency"
            ),
            color_continuous_scale=(
                "YlGnBu"
            ),
        )

        figure.update_layout(
            xaxis_title=None,
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    lifecycle_summary = (
        lifecycle.groupby(
            "LifecycleStage",
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
            AvgAOV=(
                "AOV",
                "mean",
            ),
            AvgLifetimeDays=(
                "CustomerLifetimeDays",
                "mean",
            ),
        )
    )

    with right:
        figure = px.pie(
            lifecycle_summary,
            names="LifecycleStage",
            values="Customers",
            hole=.58,
            title=(
                "Customer Lifecycle Mix"
            ),
            color_discrete_sequence=[
                COLORS[
                    "uae_green"
                ],
                COLORS["info"],
                COLORS["gold"],
                COLORS[
                    "uae_red"
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

    figure = px.scatter(
        lifecycle,
        x="Orders",
        y="Revenue",
        size="AOV",
        color="LifecycleStage",
        hover_name=(
            "CustomerCode"
        ),
        hover_data=[
            "CustomerLifetimeDays",
            "ReturnRatePct",
        ],
        title=(
            "Customer Lifecycle "
            "Revenue Position"
        ),
        opacity=.62,
    )

    st.plotly_chart(
        style_figure(
            figure,
            450,
        ),
        use_container_width=True,
    )


# ============================================================
# Monthly Customer Activity
# ============================================================

def _render_monthly_activity(
    activity: pd.DataFrame,
) -> None:
    if activity.empty:
        return

    section_header(
        "Customer Acquisition & Activity",
        (
            "Visible-scope new versus returning "
            "customer activity over time."
        ),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=activity[
                "MonthStart"
            ],
            y=activity[
                "NewCustomers"
            ],
            name="New Customers",
            marker_color=(
                COLORS["info"]
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=activity[
                "MonthStart"
            ],
            y=activity[
                "ReturningCustomers"
            ],
            name=(
                "Returning Customers"
            ),
            marker_color=(
                COLORS[
                    "uae_green"
                ]
            ),
        )
    )

    figure.update_layout(
        barmode="stack",
        title=(
            "New vs Returning Customers"
        ),
        xaxis_title=None,
        yaxis_title="Customers",
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
        figure = px.line(
            activity,
            x="MonthStart",
            y="ActiveCustomers",
            markers=True,
            title=(
                "Monthly Active Customers"
            ),
        )

        figure.update_traces(
            line=dict(
                color=COLORS[
                    "uae_green"
                ],
                width=3,
            )
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.line(
            activity,
            x="MonthStart",
            y=(
                "RevenuePerActiveCustomer"
            ),
            markers=True,
            title=(
                "Revenue per Active Customer"
            ),
        )

        figure.update_traces(
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=3,
            )
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )


# ============================================================
# Cohort Retention
# ============================================================

def _render_cohort_retention(
    cohort: pd.DataFrame,
    filters,
) -> None:
    if cohort.empty:
        return

    section_header(
        "Cohort Retention",
        (
            "Monthly customer cohorts and "
            "subsequent purchase retention."
        ),
    )

    if filters.start_date is not None:
        st.info(
            "A date filter is active. Cohort Month 0 "
            "is the customer's first purchase visible "
            "inside the selected analytical window, "
            "not necessarily their all-time first purchase."
        )

    cohort_display = (
        cohort[
            cohort[
                "CohortIndex"
            ]
            <= 12
        ]
        .copy()
    )

    cohort_display[
        "CohortLabel"
    ] = (
        cohort_display[
            "CohortMonth"
        ]
        .dt.strftime(
            "%Y-%m"
        )
    )

    matrix = (
        cohort_display.pivot(
            index="CohortLabel",
            columns="CohortIndex",
            values="RetentionPct",
        )
    )

    figure = px.imshow(
        matrix,
        aspect="auto",
        text_auto=".0f",
        zmin=0,
        zmax=100,
        color_continuous_scale=(
            "YlGn"
        ),
        labels={
            "x":
                "Months Since Cohort Start",
            "y":
                "Cohort",
            "color":
                "Retention %",
        },
        title=(
            "12-Month Cohort Retention Heatmap"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                500,
                len(matrix)
                * 24,
            ),
        ),
        use_container_width=True,
    )

    curve = (
        cohort_display.groupby(
            "CohortIndex",
            as_index=False,
        )
        .agg(
            AvgRetentionPct=(
                "RetentionPct",
                "mean",
            ),
            MedianRetentionPct=(
                "RetentionPct",
                "median",
            ),
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=curve[
                "CohortIndex"
            ],
            y=curve[
                "AvgRetentionPct"
            ],
            name="Average Retention",
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
            x=curve[
                "CohortIndex"
            ],
            y=curve[
                "MedianRetentionPct"
            ],
            name="Median Retention",
            mode="lines+markers",
            line=dict(
                color=COLORS[
                    "gold"
                ],
                width=2.5,
            ),
        )
    )

    figure.update_layout(
        title=(
            "Average Cohort Retention Curve"
        ),
        xaxis_title=(
            "Months Since Cohort Start"
        ),
        yaxis_title="Retention %",
    )

    st.plotly_chart(
        style_figure(
            figure,
            420,
        ),
        use_container_width=True,
    )


# ============================================================
# Cohort Revenue
# ============================================================

def _render_cohort_revenue(
    cohort_revenue: pd.DataFrame,
) -> None:
    if cohort_revenue.empty:
        return

    section_header(
        "Cohort Revenue Development",
        (
            "Revenue contribution by customer cohort "
            "and months since cohort start."
        ),
    )

    data = (
        cohort_revenue[
            cohort_revenue[
                "CohortIndex"
            ]
            <= 12
        ]
        .copy()
    )

    data[
        "CohortLabel"
    ] = (
        data[
            "CohortMonth"
        ]
        .dt.strftime(
            "%Y-%m"
        )
    )

    revenue_matrix = (
        data.pivot(
            index="CohortLabel",
            columns="CohortIndex",
            values="Revenue",
        )
        .fillna(0)
    )

    figure = px.imshow(
        revenue_matrix,
        aspect="auto",
        color_continuous_scale=(
            "YlGnBu"
        ),
        labels={
            "x":
                "Months Since Cohort Start",
            "y":
                "Cohort",
            "color":
                "Revenue",
        },
        title=(
            "12-Month Cohort Revenue Heatmap"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                500,
                len(
                    revenue_matrix
                )
                * 24,
            ),
        ),
        use_container_width=True,
    )

    cohort_total = (
        data.groupby(
            "CohortLabel",
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
        )
        .sort_values(
            "Revenue"
        )
    )

    figure = px.bar(
        cohort_total,
        x="Revenue",
        y="CohortLabel",
        orientation="h",
        color="GrossProfit",
        title=(
            "Cohort Lifetime Revenue "
            "within Visible Window"
        ),
        color_continuous_scale=(
            "Viridis"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            max(
                440,
                len(
                    cohort_total
                )
                * 22,
            ),
        ),
        use_container_width=True,
    )


# ============================================================
# CRM Action Queue
# ============================================================

def _render_action_queue(
    rfm: pd.DataFrame,
) -> None:
    section_header(
        "CRM Action Queue",
        (
            "Rule-based customer groups for retention, "
            "win-back, nurture and risk review."
        ),
    )

    action_summary = (
        rfm.groupby(
            "ActionFlag",
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
        )
    )

    figure = px.bar(
        action_summary.sort_values(
            "Revenue"
        ),
        x="Revenue",
        y="ActionFlag",
        orientation="h",
        color="ActionFlag",
        text="Customers",
        title=(
            "Revenue Exposure by CRM Action"
        ),
        color_discrete_map={
            "VIP / Retain":
                COLORS[
                    "uae_green"
                ],
            "High-Value Win-Back":
                COLORS[
                    "uae_red"
                ],
            "Nurture":
                COLORS["info"],
            "Reactivation":
                "#E88A32",
            "Return Risk Review":
                COLORS["gold"],
            "Standard":
                COLORS["muted"],
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

    priority = (
        rfm[
            rfm[
                "ActionFlag"
            ]
            != "Standard"
        ]
        .sort_values(
            [
                "CustomerValueScore",
                "Monetary",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .copy()
    )

    if priority.empty:
        st.success(
            "No priority CRM actions "
            "under the current rules."
        )
        return

    st.dataframe(
        priority[
            [
                "CustomerCode",
                "Segment",
                "ValueClass",
                "ActionFlag",
                "Recency",
                "Frequency",
                "Monetary",
                "AOV",
                "GrossProfit",
                "ReturnRatePct",
                "CustomerValueScore",
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
    rfm: pd.DataFrame,
    segment_summary: pd.DataFrame,
    activity: pd.DataFrame,
    cohort: pd.DataFrame,
) -> None:
    section_header(
        "Customer Data Explorer",
        (
            "Secure filtered customer datasets "
            "available for analysis and export."
        ),
    )

    (
        customer_tab,
        segment_tab,
        activity_tab,
        cohort_tab,
    ) = st.tabs(
        [
            "Customer RFM",
            "Segments",
            "Monthly Activity",
            "Cohorts",
        ]
    )

    with customer_tab:
        st.dataframe(
            rfm,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=rfm,
            label=(
                "Export filtered "
                "customer RFM"
            ),
            file_name=(
                "customers_rfm_filtered.csv"
            ),
            key=(
                "customers_export_rfm"
            ),
        )

    with segment_tab:
        st.dataframe(
            segment_summary,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=segment_summary,
            label=(
                "Export RFM segment summary"
            ),
            file_name=(
                "customers_rfm_segments.csv"
            ),
            key=(
                "customers_export_segments"
            ),
        )

    with activity_tab:
        st.dataframe(
            activity,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=activity,
            label=(
                "Export monthly "
                "customer activity"
            ),
            file_name=(
                "customers_monthly_activity.csv"
            ),
            key=(
                "customers_export_activity"
            ),
        )

    with cohort_tab:
        st.dataframe(
            cohort,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=cohort,
            label=(
                "Export cohort retention"
            ),
            file_name=(
                "customers_cohort_retention.csv"
            ),
            key=(
                "customers_export_cohort"
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
        "Customer, RFM & Retention Command Center",
        (
            "Advanced CRM intelligence covering customer "
            "value, RFM segmentation, repeat behavior, "
            "revenue concentration, lifecycle, acquisition "
            "and cohort retention within the secure scope."
        ),
        "UAE CUSTOMER INTELLIGENCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

    summary = (
        get_filtered_customer_summary(
            user,
            filters,
        )
    )

    raw_rfm = (
        get_filtered_customer_rfm(
            user,
            filters,
        )
    )

    if raw_rfm.empty:
        st.warning(
            "No customer purchase data "
            "matches the active filters."
        )
        return

    rfm = _prepare_customer_value(
        raw_rfm
    )

    segment_summary = (
        get_filtered_rfm_summary(
            user,
            filters,
        )
    )

    concentration = (
        get_filtered_customer_concentration(
            user,
            filters,
        )
    )

    frequency = (
        get_filtered_frequency_distribution(
            user,
            filters,
        )
    )

    lifecycle = (
        get_filtered_customer_lifecycle(
            user,
            filters,
        )
    )

    activity = (
        get_filtered_monthly_customer_activity(
            user,
            filters,
        )
    )

    cohort = (
        get_filtered_cohort_retention(
            user,
            filters,
        )
    )

    cohort_revenue = (
        get_filtered_cohort_revenue(
            user,
            filters,
        )
    )

    _render_kpis(
        summary,
        rfm,
    )

    _render_signals(
        rfm,
        concentration,
    )

    _render_rfm_overview(
        rfm,
        segment_summary,
    )

    _render_rf_heatmap(
        rfm
    )

    _render_customer_value(
        rfm
    )

    _render_concentration(
        concentration
    )

    _render_frequency(
        frequency,
        lifecycle,
    )

    _render_monthly_activity(
        activity
    )

    _render_cohort_retention(
        cohort,
        filters,
    )

    _render_cohort_revenue(
        cohort_revenue
    )

    _render_action_queue(
        rfm
    )

    _render_data_explorer(
        user,
        rfm,
        segment_summary,
        activity,
        cohort,
    )