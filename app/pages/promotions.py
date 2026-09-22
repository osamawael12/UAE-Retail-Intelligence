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
from src.analytics.promotion_data import (
    get_campaign_performance,
    get_discount_band_summary,
    get_monthly_promotion_trend,
    get_promotion_category_performance,
    get_promotion_emirate_performance,
    get_promotion_kpis,
    get_promotion_product_performance,
    get_promotion_status_summary,
    get_promotion_store_performance,
    get_promotion_type_summary,
    get_seasonal_campaign_family_summary,
    get_seasonal_campaigns,
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
        result = float(
            value
        )
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


def _safe_percentage_difference(
    first,
    second,
) -> float | None:
    first_value = _safe_float(
        first
    )

    second_value = _safe_float(
        second
    )

    if second_value == 0:
        return None

    return (
        (
            first_value
            - second_value
        )
        / abs(
            second_value
        )
        * 100
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


def _get_status_value(
    status: pd.DataFrame,
    promotion_status: str,
    column: str,
) -> float | None:
    if (
        status.empty
        or column
        not in status.columns
    ):
        return None

    rows = status.loc[
        status[
            "PromotionStatus"
        ]
        == promotion_status,
        column,
    ]

    if rows.empty:
        return None

    return _safe_float(
        rows.iloc[0]
    )


def _campaign_family(
    name: str,
) -> str:
    value = str(
        name
    ).lower()

    if "ramadan" in value:
        return "Ramadan"

    if "eid al fitr" in value:
        return "Eid Al Fitr"

    if "eid al adha" in value:
        return "Eid Al Adha"

    if "white friday" in value:
        return "White Friday"

    if "etihad" in value:
        return "Eid Al Etihad"

    if "summer" in value:
        return "Summer"

    if "year end" in value:
        return "Year End"

    return "Other Seasonal"


def _tone_from_difference(
    value,
    positive_is_good: bool = True,
) -> str:
    if value is None:
        return "gold"

    numeric = _safe_float(
        value
    )

    if positive_is_good:
        return (
            "green"
            if numeric >= 0
            else "red"
        )

    return (
        "green"
        if numeric <= 0
        else "red"
    )


# ============================================================
# Data Preparation
# ============================================================

def _prepare_campaigns(
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    data = campaigns.copy()

    if data.empty:
        return data

    data = (
        data.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

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
        "CumulativeRevenuePct"
    ] = (
        data[
            "Revenue"
        ]
        .cumsum()
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    data[
        "CampaignTier"
    ] = pd.cut(
        data[
            "CampaignScore"
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
        "CampaignFamily"
    ] = (
        data[
            "PromotionName"
        ]
        .apply(
            _campaign_family
        )
    )

    data[
        "RevenueRank"
    ] = (
        data[
            "Revenue"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    data[
        "ProfitRank"
    ] = (
        data[
            "GrossProfit"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    data[
        "ScoreRank"
    ] = (
        data[
            "CampaignScore"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return data


def _prepare_monthly(
    monthly: pd.DataFrame,
) -> pd.DataFrame:
    data = monthly.copy()

    if data.empty:
        return data

    data = (
        data.sort_values(
            [
                "PromotionStatus",
                "MonthStart",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    data[
        "Revenue3MMA"
    ] = (
        data.groupby(
            "PromotionStatus"
        )[
            "Revenue"
        ]
        .transform(
            lambda series:
                series.rolling(
                    3,
                    min_periods=1,
                )
                .mean()
        )
    )

    return data


# ============================================================
# KPI Section
# ============================================================

def _render_kpis(
    kpis: dict,
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Promotion KPI Pulse",
        (
            "Campaign penetration, promoted revenue "
            "and discount economics within the "
            "active business scope."
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Promoted Revenue",
        money(
            kpis.get(
                "PromotedRevenue"
            )
        ),
    )

    metric(
        row[1],
        "Promoted Revenue Share",
        percentage(
            kpis.get(
                "PromotedRevenueSharePct"
            )
        ),
    )

    metric(
        row[2],
        "Campaigns Used",
        number(
            kpis.get(
                "PromotionsUsed"
            )
        ),
    )

    metric(
        row[3],
        "Promotion Customers",
        number(
            kpis.get(
                "PromotionCustomers"
            )
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Line Adoption",
        percentage(
            kpis.get(
                "PromotionLineAdoptionPct"
            )
        ),
    )

    metric(
        row[1],
        "Order Adoption",
        percentage(
            kpis.get(
                "PromotionOrderAdoptionPct"
            )
        ),
    )

    metric(
        row[2],
        "Customer Penetration",
        percentage(
            kpis.get(
                "PromotionCustomerPenetrationPct"
            )
        ),
    )

    metric(
        row[3],
        "Promoted Margin",
        percentage(
            kpis.get(
                "PromotedGrossMarginPct"
            )
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Total Discount",
        money(
            kpis.get(
                "DiscountAmount"
            )
        ),
    )

    metric(
        row[1],
        "Overall Discount Rate",
        percentage(
            kpis.get(
                "OverallDiscountRatePct"
            )
        ),
    )

    metric(
        row[2],
        "Return Rate",
        percentage(
            kpis.get(
                "OverallReturnRatePct"
            )
        ),
    )

    metric(
        row[3],
        "Visible Campaign Rows",
        number(
            len(campaigns)
        ),
    )


# ============================================================
# Management Signals
# ============================================================

def _render_signals(
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Commercial Campaign Signals",
        (
            "High-level campaign opportunities "
            "and risk indicators."
        ),
    )

    top_revenue = (
        campaigns.sort_values(
            "Revenue",
            ascending=False,
        )
        .iloc[0]
    )

    top_score = (
        campaigns.sort_values(
            "CampaignScore",
            ascending=False,
        )
        .iloc[0]
    )

    margin_pressure = int(
        campaigns[
            "BusinessFlag"
        ]
        .eq(
            "High Revenue / "
            "Margin Pressure"
        )
        .sum()
    )

    return_risk = int(
        campaigns[
            "BusinessFlag"
        ]
        .eq(
            "Return Risk"
        )
        .sum()
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "TOP REVENUE CAMPAIGN",
            str(
                top_revenue[
                    "PromotionName"
                ]
            ),
            money(
                top_revenue[
                    "Revenue"
                ]
            ),
            "green",
        )

    with columns[1]:
        insight_card(
            "TOP CAMPAIGN SCORE",
            str(
                top_score[
                    "PromotionName"
                ]
            ),
            (
                f"{_safe_float(top_score['CampaignScore']):.1f}/100"
            ),
            "green",
        )

    with columns[2]:
        insight_card(
            "MARGIN PRESSURE",
            number(
                margin_pressure
            ),
            (
                "High-revenue campaigns "
                "with weak margin."
            ),
            (
                "red"
                if margin_pressure
                else "green"
            ),
        )

    with columns[3]:
        insight_card(
            "RETURN RISK",
            number(
                return_risk
            ),
            (
                "Campaigns with elevated "
                "return exposure."
            ),
            (
                "red"
                if return_risk
                else "green"
            ),
        )


# ============================================================
# Promoted vs Non-Promoted
# ============================================================

def _render_status_analysis(
    status: pd.DataFrame,
) -> None:
    section_header(
        "Promoted vs Non-Promoted Economics",
        (
            "Observed commercial differences between "
            "promoted and non-promoted sales. "
            "This is descriptive, not causal lift."
        ),
    )

    promoted_margin = (
        _get_status_value(
            status,
            "Promoted",
            "GrossMarginPct",
        )
    )

    base_margin = (
        _get_status_value(
            status,
            "Non-Promoted",
            "GrossMarginPct",
        )
    )

    promoted_revenue_line = (
        _get_status_value(
            status,
            "Promoted",
            "RevenuePerLine",
        )
    )

    base_revenue_line = (
        _get_status_value(
            status,
            "Non-Promoted",
            "RevenuePerLine",
        )
    )

    promoted_units_line = (
        _get_status_value(
            status,
            "Promoted",
            "UnitsPerLine",
        )
    )

    base_units_line = (
        _get_status_value(
            status,
            "Non-Promoted",
            "UnitsPerLine",
        )
    )

    promoted_return = (
        _get_status_value(
            status,
            "Promoted",
            "ReturnRatePct",
        )
    )

    base_return = (
        _get_status_value(
            status,
            "Non-Promoted",
            "ReturnRatePct",
        )
    )

    margin_gap = (
        (
            promoted_margin
            - base_margin
        )
        if (
            promoted_margin
            is not None
            and base_margin
            is not None
        )
        else None
    )

    revenue_line_difference = (
        _safe_percentage_difference(
            promoted_revenue_line,
            base_revenue_line,
        )
    )

    units_line_difference = (
        _safe_percentage_difference(
            promoted_units_line,
            base_units_line,
        )
    )

    return_gap = (
        (
            promoted_return
            - base_return
        )
        if (
            promoted_return
            is not None
            and base_return
            is not None
        )
        else None
    )

    signals = st.columns(4)

    with signals[0]:
        insight_card(
            "MARGIN DIFFERENCE",
            (
                f"{margin_gap:+.2f} pp"
                if margin_gap
                is not None
                else "N/A"
            ),
            (
                "Promoted margin minus "
                "non-promoted margin."
            ),
            _tone_from_difference(
                margin_gap,
            ),
        )

    with signals[1]:
        insight_card(
            "REVENUE / LINE DIFFERENCE",
            (
                percentage(
                    revenue_line_difference,
                    signed=True,
                )
                if revenue_line_difference
                is not None
                else "N/A"
            ),
            (
                "Observed promoted vs "
                "non-promoted line value."
            ),
            _tone_from_difference(
                revenue_line_difference,
            ),
        )

    with signals[2]:
        insight_card(
            "UNITS / LINE DIFFERENCE",
            (
                percentage(
                    units_line_difference,
                    signed=True,
                )
                if units_line_difference
                is not None
                else "N/A"
            ),
            (
                "Observed difference in "
                "line-level unit volume."
            ),
            _tone_from_difference(
                units_line_difference,
            ),
        )

    with signals[3]:
        insight_card(
            "RETURN RATE GAP",
            (
                f"{return_gap:+.2f} pp"
                if return_gap
                is not None
                else "N/A"
            ),
            (
                "Promoted return rate minus "
                "non-promoted return rate."
            ),
            _tone_from_difference(
                return_gap,
                positive_is_good=False,
            ),
        )

    left, right = st.columns(2)

    with left:
        financial = (
            status[
                [
                    "PromotionStatus",
                    "Revenue",
                    "GrossProfit",
                ]
            ]
            .melt(
                id_vars=[
                    "PromotionStatus"
                ],
                var_name="Metric",
                value_name="AED",
            )
        )

        figure = px.bar(
            financial,
            x="PromotionStatus",
            y="AED",
            color="Metric",
            barmode="group",
            title=(
                "Revenue & Gross Profit"
            ),
            color_discrete_map={
                "Revenue":
                    COLORS[
                        "uae_green"
                    ],
                "GrossProfit":
                    COLORS["gold"],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    with right:
        profile = (
            status[
                [
                    "PromotionStatus",
                    "GrossMarginPct",
                    "DiscountRatePct",
                    "ReturnRatePct",
                ]
            ]
            .melt(
                id_vars=[
                    "PromotionStatus"
                ],
                var_name="Metric",
                value_name="Percent",
            )
        )

        figure = px.bar(
            profile,
            x="Metric",
            y="Percent",
            color="PromotionStatus",
            barmode="group",
            title=(
                "Margin / Discount / Return Profile"
            ),
            color_discrete_map={
                "Promoted":
                    COLORS[
                        "uae_green"
                    ],
                "Non-Promoted":
                    COLORS[
                        "muted"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )


# ============================================================
# Monthly Trend
# ============================================================

def _render_monthly_analysis(
    monthly: pd.DataFrame,
) -> None:
    if monthly.empty:
        return

    section_header(
        "Monthly Promotion Trend",
        (
            "Revenue, profit and promotion contribution "
            "through time."
        ),
    )

    figure = px.line(
        monthly,
        x="MonthStart",
        y="Revenue",
        color="PromotionStatus",
        markers=True,
        title=(
            "Monthly Revenue: Promoted "
            "vs Non-Promoted"
        ),
        color_discrete_map={
            "Promoted":
                COLORS[
                    "uae_green"
                ],
            "Non-Promoted":
                COLORS[
                    "muted"
                ],
        },
    )

    st.plotly_chart(
        style_figure(
            figure,
            460,
        ),
        use_container_width=True,
    )

    pivot = (
        monthly.pivot_table(
            index="MonthStart",
            columns="PromotionStatus",
            values="Revenue",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    if "Promoted" not in pivot:
        pivot[
            "Promoted"
        ] = 0

    if (
        "Non-Promoted"
        not in pivot
    ):
        pivot[
            "Non-Promoted"
        ] = 0

    pivot[
        "TotalRevenue"
    ] = (
        pivot["Promoted"]
        + pivot["Non-Promoted"]
    )

    pivot[
        "PromotionRevenueSharePct"
    ] = np.where(
        pivot[
            "TotalRevenue"
        ] != 0,
        pivot[
            "Promoted"
        ]
        * 100
        / pivot[
            "TotalRevenue"
        ],
        0,
    )

    left, right = st.columns(2)

    with left:
        figure = px.area(
            pivot,
            x="MonthStart",
            y=(
                "PromotionRevenueSharePct"
            ),
            title=(
                "Monthly Promoted Revenue Share"
            ),
        )

        figure.update_traces(
            line_color=(
                COLORS[
                    "uae_green"
                ]
            ),
            fillcolor=(
                "rgba(0,132,61,.13)"
            ),
        )

        figure.update_layout(
            yaxis_title="Share %",
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )

    with right:
        promoted = (
            monthly[
                monthly[
                    "PromotionStatus"
                ]
                == "Promoted"
            ]
            .copy()
        )

        if not promoted.empty:
            figure = go.Figure()

            figure.add_trace(
                go.Scatter(
                    x=promoted[
                        "MonthStart"
                    ],
                    y=promoted[
                        "Revenue"
                    ],
                    name=(
                        "Promoted Revenue"
                    ),
                    line=dict(
                        color=COLORS[
                            "uae_green"
                        ],
                        width=2,
                    ),
                )
            )

            figure.add_trace(
                go.Scatter(
                    x=promoted[
                        "MonthStart"
                    ],
                    y=promoted[
                        "Revenue3MMA"
                    ],
                    name="3M Average",
                    line=dict(
                        color=COLORS[
                            "gold"
                        ],
                        width=3,
                    ),
                )
            )

            figure.update_layout(
                title=(
                    "Promoted Revenue Momentum"
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
# Promotion Type
# ============================================================

def _render_type_analysis(
    types: pd.DataFrame,
) -> None:
    if types.empty:
        return

    section_header(
        "Promotion Type Economics",
        (
            "SEASONAL, PRODUCT, CATEGORY and STORE "
            "campaign performance."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            types.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="PromotionType",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "Campaigns",
                "Orders",
                "Customers",
                "DiscountRatePct",
                "ReturnRatePct",
                "RevenuePerCampaign",
            ],
            title=(
                "Revenue by Promotion Type"
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

    with right:
        figure = px.scatter(
            types,
            x="DiscountRatePct",
            y="GrossMarginPct",
            size="Revenue",
            color="PromotionType",
            hover_data=[
                "RevenuePerCampaign",
                "ReturnRatePct",
            ],
            title=(
                "Type Discount / Margin Matrix"
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
# Campaign Ranking
# ============================================================

def _render_campaign_ranking(
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Campaign Ranking & Economics",
        (
            "Campaign revenue, profit, margin "
            "and relative commercial score."
        ),
    )

    count = min(
        20,
        len(campaigns),
    )

    left, right = st.columns(2)

    with left:
        top_revenue = (
            campaigns.nlargest(
                count,
                "Revenue",
            )
            .sort_values(
                "Revenue"
            )
        )

        figure = px.bar(
            top_revenue,
            x="Revenue",
            y="PromotionName",
            orientation="h",
            color="PromotionType",
            hover_data=[
                "GrossProfit",
                "GrossMarginPct",
                "DiscountRatePct",
                "ReturnRatePct",
                "CampaignScore",
            ],
            title=(
                "Top Campaigns by Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                620,
            ),
            use_container_width=True,
        )

    with right:
        top_profit = (
            campaigns.nlargest(
                count,
                "GrossProfit",
            )
            .sort_values(
                "GrossProfit"
            )
        )

        figure = px.bar(
            top_profit,
            x="GrossProfit",
            y="PromotionName",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "Revenue",
                "DiscountRatePct",
                "CampaignScore",
            ],
            title=(
                "Top Campaigns by Gross Profit"
            ),
            color_continuous_scale=(
                "YlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                620,
            ),
            use_container_width=True,
        )

    figure = px.scatter(
        campaigns,
        x="Revenue",
        y="GrossMarginPct",
        size="Customers",
        color="BusinessFlag",
        hover_name="PromotionName",
        hover_data=[
            "PromotionType",
            "DiscountRatePct",
            "ReturnRatePct",
            "RevenuePerOrder",
            "CampaignScore",
        ],
        title=(
            "Campaign Revenue / Margin Matrix"
        ),
        color_discrete_map={
            "Normal":
                COLORS[
                    "muted"
                ],

            "High Revenue / Margin Pressure":
                COLORS[
                    "gold"
                ],

            "Return Risk":
                COLORS[
                    "uae_red"
                ],

            "Deep Discount / Margin Risk":
                "#E88A32",

            "High Revenue / Healthy Margin":
                COLORS[
                    "uae_green"
                ],
        },
        opacity=.76,
    )

    st.plotly_chart(
        style_figure(
            figure,
            520,
        ),
        use_container_width=True,
    )


# ============================================================
# Campaign Score
# ============================================================

def _render_campaign_score(
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Campaign Performance Score",
        (
            "Relative portfolio score combining "
            "revenue, profit, margin, customers, "
            "return health and discount health."
        ),
    )

    count = min(
        35,
        len(campaigns),
    )

    top = (
        campaigns.nlargest(
            count,
            "CampaignScore",
        )
        .sort_values(
            "CampaignScore"
        )
    )

    figure = px.bar(
        top,
        x="CampaignScore",
        y="PromotionName",
        orientation="h",
        color="CampaignTier",
        hover_data=[
            "PromotionType",
            "Revenue",
            "GrossProfit",
            "GrossMarginPct",
            "DiscountRatePct",
            "ReturnRatePct",
        ],
        title=(
            "Relative Campaign Score"
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
                600,
                count * 24,
            ),
        ),
        use_container_width=True,
    )

    st.caption(
        "Campaign Score is a relative management "
        "prioritization metric, not a causal ROI or "
        "incrementality measure."
    )


# ============================================================
# Discount Analysis
# ============================================================

def _render_discount_analysis(
    discounts: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Discount Depth Intelligence",
        (
            "Observed relationship between "
            "discount depth, revenue, margin "
            "and returns."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            discounts,
            x="DiscountBand",
            y="Revenue",
            color="GrossMarginPct",
            hover_data=[
                "SalesLines",
                "GrossUnits",
                "ReturnRatePct",
                "RevenuePerLine",
            ],
            title=(
                "Revenue by Discount Band"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        figure.update_layout(
            xaxis_title=None,
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
                x=discounts[
                    "DiscountBand"
                ],
                y=discounts[
                    "GrossMarginPct"
                ],
                name="Gross Margin %",
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
                x=discounts[
                    "DiscountBand"
                ],
                y=discounts[
                    "ReturnRatePct"
                ],
                name="Return Rate %",
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "uae_red"
                    ],
                    width=2.5,
                ),
            )
        )

        figure.update_layout(
            title=(
                "Margin & Return Profile "
                "by Discount Band"
            ),
            yaxis_title="Percent",
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    figure = px.scatter(
        campaigns,
        x="DiscountRatePct",
        y="GrossMarginPct",
        size="Revenue",
        color="PromotionType",
        hover_name="PromotionName",
        hover_data=[
            "Orders",
            "Customers",
            "ReturnRatePct",
            "CampaignScore",
        ],
        title=(
            "Campaign Discount vs Margin"
        ),
        opacity=.72,
    )

    trend_data = (
        campaigns[
            [
                "DiscountRatePct",
                "GrossMarginPct",
            ]
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

    if len(
        trend_data
    ) >= 2:
        x = (
            trend_data[
                "DiscountRatePct"
            ].to_numpy(
                dtype=float
            )
        )

        y = (
            trend_data[
                "GrossMarginPct"
            ].to_numpy(
                dtype=float
            )
        )

        if np.std(x) > 0:
            slope, intercept = (
                np.polyfit(
                    x,
                    y,
                    1,
                )
            )

            x_line = np.linspace(
                x.min(),
                x.max(),
                100,
            )

            y_line = (
                slope
                * x_line
                + intercept
            )

            figure.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name=(
                        "Descriptive Trend"
                    ),
                    line=dict(
                        color=COLORS[
                            "gold"
                        ],
                        dash="dash",
                        width=3,
                    ),
                )
            )

    st.plotly_chart(
        style_figure(
            figure,
            500,
        ),
        use_container_width=True,
    )

    st.caption(
        "The fitted line is descriptive only. "
        "It is not an elasticity estimate and "
        "does not identify causal discount effects."
    )


# ============================================================
# UAE Seasonal Campaigns
# ============================================================

def _render_seasonal_analysis(
    seasonal: pd.DataFrame,
    families: pd.DataFrame,
) -> None:
    section_header(
        "UAE Seasonal Campaign Intelligence",
        (
            "Ramadan, Eid Al Fitr, Eid Al Adha, "
            "White Friday, Eid Al Etihad, Summer "
            "and Year End campaign performance."
        ),
    )

    if seasonal.empty:
        st.info(
            "No seasonal campaign activity "
            "matches the active filters."
        )
        return

    plot_data = seasonal.copy()

    plot_data[
        "CampaignFamily"
    ] = (
        plot_data[
            "PromotionName"
        ]
        .apply(
            _campaign_family
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            plot_data.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="PromotionName",
            orientation="h",
            color="CampaignFamily",
            hover_data=[
                "Orders",
                "Customers",
                "DiscountRatePct",
                "GrossMarginPct",
                "ReturnRatePct",
            ],
            title=(
                "Seasonal Campaign Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                max(
                    530,
                    len(
                        plot_data
                    )
                    * 25,
                ),
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            plot_data,
            x="DiscountRatePct",
            y="GrossMarginPct",
            size="Revenue",
            color="CampaignFamily",
            hover_name="PromotionName",
            hover_data=[
                "ReturnRatePct",
                "CampaignScore",
            ],
            title=(
                "Seasonal Discount / Margin"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                max(
                    530,
                    len(
                        plot_data
                    )
                    * 25,
                ),
            ),
            use_container_width=True,
        )

    if not families.empty:
        figure = px.bar(
            families.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="CampaignFamily",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "Campaigns",
                "Orders",
                "Customers",
                "DiscountRatePct",
                "ReturnRatePct",
                "RevenuePerCampaign",
            ],
            title=(
                "Seasonal Family Performance "
                "Across Visible Years"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
            ),
            use_container_width=True,
        )


# ============================================================
# Category / Product
# ============================================================

def _render_merchandise_analysis(
    categories: pd.DataFrame,
    products: pd.DataFrame,
) -> None:
    section_header(
        "Promotion Merchandise Intelligence",
        (
            "Categories and SKUs generating "
            "promoted commercial value."
        ),
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            categories.sort_values(
                "Revenue"
            ),
            x="Revenue",
            y="CategoryName",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "Campaigns",
                "Orders",
                "DiscountRatePct",
                "ReturnRatePct",
            ],
            title=(
                "Promoted Revenue by Category"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            categories,
            x="Revenue",
            y="GrossMarginPct",
            size="GrossUnits",
            color="ReturnRatePct",
            hover_name="CategoryName",
            hover_data=[
                "DiscountRatePct",
                "Campaigns",
            ],
            title=(
                "Category Promotion Matrix"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                450,
            ),
            use_container_width=True,
        )

    if not products.empty:
        top_products = (
            products.nlargest(
                min(
                    25,
                    len(products),
                ),
                "Revenue",
            )
            .sort_values(
                "Revenue"
            )
        )

        figure = px.bar(
            top_products,
            x="Revenue",
            y="SKU",
            orientation="h",
            color="GrossMarginPct",
            hover_name="ProductName",
            hover_data=[
                "CategoryName",
                "BrandName",
                "Campaigns",
                "DiscountRatePct",
                "ReturnRatePct",
            ],
            title=(
                "Top Promoted Products"
            ),
            color_continuous_scale=(
                "Viridis"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                620,
            ),
            use_container_width=True,
        )


# ============================================================
# Geography
# ============================================================

def _render_geography(
    emirates: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    section_header(
        "UAE Promotion Geography",
        (
            "Campaign revenue and economics across "
            "the visible emirates and stores."
        ),
    )

    left, right = st.columns(2)

    with left:
        if not emirates.empty:
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
                hover_data=[
                    "Campaigns",
                    "Stores",
                    "Customers",
                    "GrossMarginPct",
                    "DiscountRatePct",
                ],
                title=(
                    "Promoted Revenue by Emirate"
                ),
            )

            figure.update_layout(
                showlegend=False,
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
        if not stores.empty:
            figure = px.scatter(
                stores,
                x="Revenue",
                y="GrossMarginPct",
                size="Orders",
                color="EmirateName",
                color_discrete_map=(
                    EMIRATE_COLORS
                ),
                hover_name="StoreName",
                hover_data=[
                    "StoreCode",
                    "Campaigns",
                    "ReturnRatePct",
                    "DiscountRatePct",
                ],
                title=(
                    "Store Promotion "
                    "Revenue / Margin"
                ),
            )

            st.plotly_chart(
                style_figure(
                    figure,
                    450,
                ),
                use_container_width=True,
            )

    if not stores.empty:
        top = (
            stores.nlargest(
                min(
                    20,
                    len(stores),
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
                "Campaigns",
                "GrossMarginPct",
                "ReturnRatePct",
            ],
            title=(
                "Top Stores by Promoted Revenue"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                520,
            ),
            use_container_width=True,
        )


# ============================================================
# Campaign Risk & Outliers
# ============================================================

def _render_risk_analysis(
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Campaign Risk & Outlier Screening",
        (
            "Rule-based commercial flags and "
            "statistical candidates requiring review."
        ),
    )

    flags = (
        campaigns.groupby(
            "BusinessFlag",
            as_index=False,
        )
        .agg(
            Campaigns=(
                "PromotionId",
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

    figure = px.bar(
        flags,
        x="BusinessFlag",
        y="Campaigns",
        color="BusinessFlag",
        text="Campaigns",
        hover_data=[
            "Revenue",
            "GrossProfit",
        ],
        title=(
            "Campaign Business Flags"
        ),
        color_discrete_map={
            "Normal":
                COLORS[
                    "muted"
                ],

            "High Revenue / Margin Pressure":
                COLORS[
                    "gold"
                ],

            "Return Risk":
                COLORS[
                    "uae_red"
                ],

            "Deep Discount / Margin Risk":
                "#E88A32",

            "High Revenue / Healthy Margin":
                COLORS[
                    "uae_green"
                ],
        },
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

    outliers = (
        campaigns[
            (
                campaigns[
                    "RevenueZScore"
                ].abs()
                >= 2
            )
            | (
                campaigns[
                    "MarginZScore"
                ].abs()
                >= 2
            )
            | (
                campaigns[
                    "ReturnZScore"
                ]
                >= 2
            )
        ]
        .copy()
    )

    row = st.columns(3)

    metric(
        row[0],
        "Revenue Outliers",
        number(
            (
                campaigns[
                    "RevenueZScore"
                ].abs()
                >= 2
            ).sum()
        ),
    )

    metric(
        row[1],
        "Margin Outliers",
        number(
            (
                campaigns[
                    "MarginZScore"
                ].abs()
                >= 2
            ).sum()
        ),
    )

    metric(
        row[2],
        "Return Risk Outliers",
        number(
            (
                campaigns[
                    "ReturnZScore"
                ]
                >= 2
            ).sum()
        ),
    )

    if not outliers.empty:
        st.dataframe(
            outliers[
                [
                    "PromotionCode",
                    "PromotionName",
                    "PromotionType",
                    "Revenue",
                    "GrossProfit",
                    "GrossMarginPct",
                    "DiscountRatePct",
                    "ReturnRatePct",
                    "CampaignScore",
                    "BusinessFlag",
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
# Correlation
# ============================================================

def _render_correlation(
    campaigns: pd.DataFrame,
) -> None:
    section_header(
        "Campaign Correlation Diagnostics",
        (
            "Descriptive association between "
            "campaign commercial metrics."
        ),
    )

    columns = [
        "Revenue",
        "GrossProfit",
        "GrossMarginPct",
        "DiscountRatePct",
        "ReturnRatePct",
        "Orders",
        "Customers",
        "GrossUnits",
        "RevenuePerOrder",
        "RevenuePerDay",
        "CampaignScore",
    ]

    available = [
        column
        for column in columns
        if column
        in campaigns.columns
    ]

    correlation = (
        campaigns[
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
            "Campaign KPI Correlation Matrix"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            650,
        ),
        use_container_width=True,
    )

    st.caption(
        "Correlation is descriptive and does not "
        "establish campaign causality."
    )


# ============================================================
# Data Explorer
# ============================================================

def _render_data_explorer(
    user,
    campaigns: pd.DataFrame,
    types: pd.DataFrame,
    seasonal: pd.DataFrame,
    categories: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    section_header(
        "Promotion Data Explorer",
        (
            "Secure filtered campaign datasets "
            "available for review and export."
        ),
    )

    (
        campaign_tab,
        type_tab,
        seasonal_tab,
        merchandise_tab,
        store_tab,
    ) = st.tabs(
        [
            "Campaigns",
            "Types",
            "Seasonal",
            "Products",
            "Stores",
        ]
    )

    with campaign_tab:
        st.dataframe(
            campaigns,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=campaigns,
            label=(
                "Export filtered campaigns"
            ),
            file_name=(
                "promotions_campaigns_filtered.csv"
            ),
            key=(
                "promotions_export_campaigns"
            ),
        )

    with type_tab:
        st.dataframe(
            types,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=types,
            label=(
                "Export promotion types"
            ),
            file_name=(
                "promotions_types_filtered.csv"
            ),
            key=(
                "promotions_export_types"
            ),
        )

    with seasonal_tab:
        st.dataframe(
            seasonal,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=seasonal,
            label=(
                "Export seasonal campaigns"
            ),
            file_name=(
                "promotions_seasonal_filtered.csv"
            ),
            key=(
                "promotions_export_seasonal"
            ),
        )

    with merchandise_tab:
        st.dataframe(
            products,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=products,
            label=(
                "Export promoted products"
            ),
            file_name=(
                "promotions_products_filtered.csv"
            ),
            key=(
                "promotions_export_products"
            ),
        )

    with store_tab:
        st.dataframe(
            stores,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=stores,
            label=(
                "Export store promotion performance"
            ),
            file_name=(
                "promotions_stores_filtered.csv"
            ),
            key=(
                "promotions_export_stores"
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
        "Promotions & Campaign Command Center",
        (
            "Advanced UAE campaign intelligence covering "
            "promotion adoption, campaign economics, "
            "discount depth, margin pressure, seasonal "
            "campaigns, merchandise, geography and risk."
        ),
        "UAE COMMERCIAL CAMPAIGN INTELLIGENCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

    st.info(
        "Campaign comparisons are descriptive associations. "
        "They should not be interpreted as causal promotion "
        "lift, incremental revenue, or ROI estimates."
    )

    kpis = get_promotion_kpis(
        user,
        filters,
    )

    status = (
        get_promotion_status_summary(
            user,
            filters,
        )
    )

    types = (
        get_promotion_type_summary(
            user,
            filters,
        )
    )

    raw_campaigns = (
        get_campaign_performance(
            user,
            filters,
        )
    )

    if raw_campaigns.empty:
        st.warning(
            "No promoted sales match "
            "the active analytical filters."
        )
        return

    campaigns = _prepare_campaigns(
        raw_campaigns
    )

    discounts = (
        get_discount_band_summary(
            user,
            filters,
        )
    )

    monthly = _prepare_monthly(
        get_monthly_promotion_trend(
            user,
            filters,
        )
    )

    seasonal = (
        get_seasonal_campaigns(
            user,
            filters,
        )
    )

    families = (
        get_seasonal_campaign_family_summary(
            user,
            filters,
        )
    )

    categories = (
        get_promotion_category_performance(
            user,
            filters,
        )
    )

    products = (
        get_promotion_product_performance(
            user,
            filters,
        )
    )

    emirates = (
        get_promotion_emirate_performance(
            user,
            filters,
        )
    )

    stores = (
        get_promotion_store_performance(
            user,
            filters,
        )
    )

    _render_kpis(
        kpis,
        campaigns,
    )

    _render_signals(
        campaigns
    )

    _render_status_analysis(
        status
    )

    _render_monthly_analysis(
        monthly
    )

    _render_type_analysis(
        types
    )

    _render_campaign_ranking(
        campaigns
    )

    _render_campaign_score(
        campaigns
    )

    _render_discount_analysis(
        discounts,
        campaigns,
    )

    _render_seasonal_analysis(
        seasonal,
        families,
    )

    _render_merchandise_analysis(
        categories,
        products,
    )

    _render_geography(
        emirates,
        stores,
    )

    _render_risk_analysis(
        campaigns
    )

    _render_correlation(
        campaigns
    )

    _render_data_explorer(
        user,
        campaigns,
        types,
        seasonal,
        categories,
        products,
        stores,
    )