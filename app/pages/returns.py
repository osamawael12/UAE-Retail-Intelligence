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
from src.analytics.filtered_data import (
    get_filtered_returns,
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
        value = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if not math.isfinite(value):
        return default

    return value


def _period_label(
    filters,
) -> str:
    if (
        filters.start_date is not None
        and filters.end_date is not None
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
    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    std = values.std(
        ddof=0
    )

    if (
        pd.isna(std)
        or std == 0
    ):
        return pd.Series(
            np.zeros(
                len(values)
            ),
            index=values.index,
        )

    return (
        values
        - values.mean()
    ) / std


def _min_max(
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

    if minimum == maximum:
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
        score = 100 - score

    return score


def _aggregate_returns(
    data: pd.DataFrame,
    groups: list[str],
) -> pd.DataFrame:
    summary = (
        data.groupby(
            groups,
            as_index=False,
            dropna=False,
        )
        .agg(
            ReturnLines=(
                "ReturnItemId",
                "count",
            ),
            Returns=(
                "ReturnId",
                "nunique",
            ),
            Orders=(
                "OrderId",
                "nunique",
            ),
            Customers=(
                "CustomerId",
                "nunique",
            ),
            ReturnedUnits=(
                "ReturnQuantity",
                "sum",
            ),
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            RefundAmount=(
                "RefundAmount",
                "sum",
            ),
            ReturnedCOGS=(
                "ReturnedCOGS",
                "sum",
            ),
            AvgReturnLagDays=(
                "ReturnLagDays",
                "mean",
            ),
            RestockableLines=(
                "IsRestockable",
                "sum",
            ),
        )
    )

    summary[
        "RefundPctOfReturnedValue"
    ] = np.where(
        summary[
            "ReturnedValue"
        ] != 0,
        summary[
            "RefundAmount"
        ]
        * 100
        / summary[
            "ReturnedValue"
        ],
        0,
    )

    summary[
        "RestockableLinePct"
    ] = np.where(
        summary[
            "ReturnLines"
        ] != 0,
        summary[
            "RestockableLines"
        ]
        * 100
        / summary[
            "ReturnLines"
        ],
        0,
    )

    return summary


# ============================================================
# Preparation
# ============================================================

def _prepare_returns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    data = dataframe.copy()

    if data.empty:
        return data

    data[
        "ReturnDate"
    ] = pd.to_datetime(
        data[
            "ReturnDate"
        ]
    )

    data[
        "OrderDate"
    ] = pd.to_datetime(
        data[
            "OrderDate"
        ]
    )

    data[
        "ReturnMonth"
    ] = (
        data[
            "ReturnDate"
        ]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    data[
        "ReturnYear"
    ] = (
        data[
            "ReturnDate"
        ]
        .dt.year
    )

    data[
        "ReturnDayName"
    ] = (
        data[
            "ReturnDate"
        ]
        .dt.day_name()
    )

    data[
        "LagBand"
    ] = pd.cut(
        data[
            "ReturnLagDays"
        ],
        bins=[
            -1,
            3,
            7,
            14,
            30,
            60,
            np.inf,
        ],
        labels=[
            "0-3 Days",
            "4-7 Days",
            "8-14 Days",
            "15-30 Days",
            "31-60 Days",
            "60+ Days",
        ],
    )

    data[
        "RefundCoveragePct"
    ] = np.where(
        data[
            "ReturnedNetAmount"
        ] != 0,
        data[
            "RefundAmount"
        ]
        * 100
        / data[
            "ReturnedNetAmount"
        ],
        0,
    )

    data[
        "ReturnSeverity"
    ] = (
        _min_max(
            data[
                "ReturnedNetAmount"
            ]
        )
        * .40
        + _min_max(
            data[
                "ReturnQuantity"
            ]
        )
        * .20
        + _min_max(
            data[
                "ReturnLagDays"
            ]
        )
        * .15
        + _min_max(
            data[
                "RefundAmount"
            ]
        )
        * .25
    )

    data[
        "ReturnSeverity"
    ] = (
        data[
            "ReturnSeverity"
        ]
        .clip(
            0,
            100,
        )
    )

    data[
        "SeverityTier"
    ] = pd.cut(
        data[
            "ReturnSeverity"
        ],
        bins=[
            -np.inf,
            30,
            55,
            75,
            np.inf,
        ],
        labels=[
            "Low",
            "Moderate",
            "High",
            "Critical",
        ],
    )

    data[
        "ValueZScore"
    ] = _zscore(
        data[
            "ReturnedNetAmount"
        ]
    )

    data[
        "LagZScore"
    ] = _zscore(
        data[
            "ReturnLagDays"
        ]
    )

    data[
        "QuantityZScore"
    ] = _zscore(
        data[
            "ReturnQuantity"
        ]
    )

    data[
        "AnomalyCandidate"
    ] = (
        (
            data[
                "ValueZScore"
            ]
            >= 2.5
        )
        | (
            data[
                "LagZScore"
            ]
            >= 2.5
        )
        | (
            data[
                "QuantityZScore"
            ]
            >= 2.5
        )
    )

    return data


# ============================================================
# KPIs
# ============================================================

def _render_kpis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Returns KPI Pulse",
        (
            "Post-sale exposure inside the current "
            "security and analytical scope."
        ),
    )

    returned_units = _safe_float(
        data[
            "ReturnQuantity"
        ].sum()
    )

    returned_value = _safe_float(
        data[
            "ReturnedNetAmount"
        ].sum()
    )

    refunds = _safe_float(
        data[
            "RefundAmount"
        ].sum()
    )

    returned_cogs = _safe_float(
        data[
            "ReturnedCOGS"
        ].sum()
    )

    avg_lag = _safe_float(
        data[
            "ReturnLagDays"
        ].mean()
    )

    median_lag = _safe_float(
        data[
            "ReturnLagDays"
        ].median()
    )

    restockable_pct = (
        _safe_float(
            data[
                "IsRestockable"
            ].sum()
        )
        / len(data)
        * 100
        if len(data)
        else 0
    )

    row = st.columns(4)

    metric(
        row[0],
        "Return Transactions",
        number(
            data[
                "ReturnId"
            ].nunique()
        ),
    )

    metric(
        row[1],
        "Returned Units",
        number(
            returned_units
        ),
    )

    metric(
        row[2],
        "Returned Value",
        money(
            returned_value
        ),
    )

    metric(
        row[3],
        "Refund Amount",
        money(refunds),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Returned COGS",
        money(
            returned_cogs
        ),
    )

    metric(
        row[1],
        "Average Return Lag",
        f"{avg_lag:.1f} days",
    )

    metric(
        row[2],
        "Median Return Lag",
        f"{median_lag:.1f} days",
    )

    metric(
        row[3],
        "Restockable Lines",
        percentage(
            restockable_pct
        ),
    )


# ============================================================
# Signals
# ============================================================

def _render_signals(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Management Signals"
    )

    reasons = (
        _aggregate_returns(
            data,
            [
                "ReturnReason"
            ],
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
    )

    categories = (
        _aggregate_returns(
            data,
            [
                "CategoryName"
            ],
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
    )

    stores = (
        _aggregate_returns(
            data,
            [
                "StoreCode",
                "StoreName",
            ],
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
    )

    top_reason = (
        reasons.iloc[0]
    )

    top_category = (
        categories.iloc[0]
    )

    top_store = (
        stores.iloc[0]
    )

    anomalies = int(
        data[
            "AnomalyCandidate"
        ].sum()
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "TOP RETURN REASON",
            str(
                top_reason[
                    "ReturnReason"
                ]
            ),
            money(
                top_reason[
                    "ReturnedValue"
                ]
            ),
            "red",
        )

    with columns[1]:
        insight_card(
            "TOP RETURN CATEGORY",
            str(
                top_category[
                    "CategoryName"
                ]
            ),
            money(
                top_category[
                    "ReturnedValue"
                ]
            ),
            "gold",
        )

    with columns[2]:
        insight_card(
            "HIGHEST VALUE STORE",
            str(
                top_store[
                    "StoreCode"
                ]
            ),
            money(
                top_store[
                    "ReturnedValue"
                ]
            ),
            "gold",
        )

    with columns[3]:
        insight_card(
            "ANOMALY CANDIDATES",
            number(
                anomalies
            ),
            (
                "Statistical review candidates "
                "across value, quantity or lag."
            ),
            (
                "red"
                if anomalies
                else "green"
            ),
        )


# ============================================================
# Monthly Trend
# ============================================================

def _render_monthly_trend(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Trend",
        (
            "Monthly returned value, units, "
            "refunds and return activity."
        ),
    )

    monthly = (
        data.groupby(
            "ReturnMonth",
            as_index=False,
        )
        .agg(
            Returns=(
                "ReturnId",
                "nunique",
            ),
            ReturnLines=(
                "ReturnItemId",
                "count",
            ),
            ReturnedUnits=(
                "ReturnQuantity",
                "sum",
            ),
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            RefundAmount=(
                "RefundAmount",
                "sum",
            ),
            AvgLagDays=(
                "ReturnLagDays",
                "mean",
            ),
        )
        .sort_values(
            "ReturnMonth"
        )
    )

    monthly[
        "ReturnedValue3MMA"
    ] = (
        monthly[
            "ReturnedValue"
        ]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=monthly[
                "ReturnMonth"
            ],
            y=monthly[
                "ReturnedValue"
            ],
            name="Returned Value",
            mode="lines+markers",
            line=dict(
                color=COLORS[
                    "uae_red"
                ],
                width=2.5,
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=monthly[
                "ReturnMonth"
            ],
            y=monthly[
                "ReturnedValue3MMA"
            ],
            name="3M Moving Average",
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
            "Monthly Returned Value"
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

    left, right = st.columns(2)

    with left:
        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=monthly[
                    "ReturnMonth"
                ],
                y=monthly[
                    "ReturnedUnits"
                ],
                name="Returned Units",
                marker_color=(
                    COLORS[
                        "uae_red"
                    ]
                ),
            )
        )

        figure.update_layout(
            title=(
                "Monthly Returned Units"
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
        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=monthly[
                    "ReturnMonth"
                ],
                y=monthly[
                    "RefundAmount"
                ],
                name="Refunds",
                marker_color=(
                    COLORS["gold"]
                ),
            )
        )

        figure.update_layout(
            title=(
                "Monthly Refund Value"
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
# Reasons
# ============================================================

def _render_reason_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Root-Cause Intelligence",
        (
            "Return reasons ranked by units, "
            "financial exposure and timing."
        ),
    )

    reasons = (
        _aggregate_returns(
            data,
            [
                "ReturnReason"
            ],
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
    )

    total_value = _safe_float(
        reasons[
            "ReturnedValue"
        ].sum()
    )

    reasons[
        "ReturnedValueSharePct"
    ] = (
        reasons[
            "ReturnedValue"
        ]
        / total_value
        * 100
        if total_value
        else 0
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            reasons.sort_values(
                "ReturnedValue"
            ),
            x="ReturnedValue",
            y="ReturnReason",
            orientation="h",
            color="AvgReturnLagDays",
            hover_data=[
                "ReturnedUnits",
                "RefundAmount",
                "RestockableLinePct",
                "ReturnedValueSharePct",
            ],
            title=(
                "Returned Value by Reason"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                460,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            reasons,
            x="ReturnedUnits",
            y="AvgReturnLagDays",
            size="ReturnedValue",
            color="RestockableLinePct",
            hover_name="ReturnReason",
            hover_data=[
                "RefundAmount",
                "ReturnedValueSharePct",
            ],
            title=(
                "Reason Severity Matrix"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                460,
            ),
            use_container_width=True,
        )

    figure = px.pie(
        reasons,
        names="ReturnReason",
        values="ReturnedValue",
        hole=.56,
        title=(
            "Returned Value Mix by Reason"
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
# Return Lag
# ============================================================

def _render_lag_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Timing & Lag Analysis",
        (
            "How quickly merchandise is returned "
            "after the original purchase."
        ),
    )

    lag = (
        data.groupby(
            "LagBand",
            observed=False,
            as_index=False,
        )
        .agg(
            ReturnLines=(
                "ReturnItemId",
                "count",
            ),
            ReturnedUnits=(
                "ReturnQuantity",
                "sum",
            ),
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            RefundAmount=(
                "RefundAmount",
                "sum",
            ),
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            lag,
            x="LagBand",
            y="ReturnLines",
            color="ReturnedValue",
            title=(
                "Returns by Lag Band"
            ),
            color_continuous_scale=(
                "YlOrRd"
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

    with right:
        figure = px.bar(
            lag,
            x="LagBand",
            y="ReturnedValue",
            color="RefundAmount",
            title=(
                "Returned Value by Lag Band"
            ),
            color_continuous_scale=(
                "Reds"
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

    figure = px.histogram(
        data,
        x="ReturnLagDays",
        nbins=40,
        title=(
            "Return Lag Distribution"
        ),
        color_discrete_sequence=[
            COLORS[
                "uae_red"
            ]
        ],
    )

    figure.add_vline(
        x=data[
            "ReturnLagDays"
        ].median(),
        line_dash="dash",
        line_color=(
            COLORS["gold"]
        ),
        annotation_text=(
            "Median"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            400,
        ),
        use_container_width=True,
    )


# ============================================================
# Refund Economics
# ============================================================

def _render_refund_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Refund Economics",
        (
            "Refund exposure relative to returned "
            "merchandise value and COGS."
        ),
    )

    total_returned = (
        _safe_float(
            data[
                "ReturnedNetAmount"
            ].sum()
        )
    )

    total_refund = (
        _safe_float(
            data[
                "RefundAmount"
            ].sum()
        )
    )

    total_cogs = (
        _safe_float(
            data[
                "ReturnedCOGS"
            ].sum()
        )
    )

    coverage = (
        total_refund
        / total_returned
        * 100
        if total_returned
        else 0
    )

    value_over_cogs = (
        total_returned
        - total_cogs
    )

    row = st.columns(3)

    metric(
        row[0],
        "Refund Coverage",
        percentage(
            coverage
        ),
    )

    metric(
        row[1],
        "Returned COGS",
        money(
            total_cogs
        ),
    )

    metric(
        row[2],
        "Returned Value - COGS",
        money(
            value_over_cogs
        ),
    )

    reasons = (
        data.groupby(
            "ReturnReason",
            as_index=False,
        )
        .agg(
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            RefundAmount=(
                "RefundAmount",
                "sum",
            ),
            ReturnedCOGS=(
                "ReturnedCOGS",
                "sum",
            ),
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=reasons[
                "ReturnReason"
            ],
            y=reasons[
                "ReturnedValue"
            ],
            name="Returned Value",
            marker_color=(
                COLORS[
                    "uae_red"
                ]
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=reasons[
                "ReturnReason"
            ],
            y=reasons[
                "RefundAmount"
            ],
            name="Refund Amount",
            marker_color=(
                COLORS["gold"]
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=reasons[
                "ReturnReason"
            ],
            y=reasons[
                "ReturnedCOGS"
            ],
            name="Returned COGS",
            marker_color=(
                COLORS["info"]
            ),
        )
    )

    figure.update_layout(
        barmode="group",
        title=(
            "Returned Value / Refund / "
            "COGS by Reason"
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            440,
        ),
        use_container_width=True,
    )


# ============================================================
# Restockability
# ============================================================

def _render_restockability(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Restockability Intelligence",
        (
            "Operational recovery potential "
            "from returned merchandise."
        ),
    )

    restock = (
        data.assign(
            RestockStatus=np.where(
                data[
                    "IsRestockable"
                ].astype(bool),
                "Restockable",
                "Non-Restockable",
            )
        )
        .groupby(
            "RestockStatus",
            as_index=False,
        )
        .agg(
            ReturnLines=(
                "ReturnItemId",
                "count",
            ),
            ReturnedUnits=(
                "ReturnQuantity",
                "sum",
            ),
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            ReturnedCOGS=(
                "ReturnedCOGS",
                "sum",
            ),
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.pie(
            restock,
            names="RestockStatus",
            values="ReturnedUnits",
            hole=.60,
            title=(
                "Returned Units by Restockability"
            ),
            color="RestockStatus",
            color_discrete_map={
                "Restockable":
                    COLORS[
                        "uae_green"
                    ],
                "Non-Restockable":
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                410,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            restock,
            x="RestockStatus",
            y="ReturnedValue",
            color="RestockStatus",
            title=(
                "Returned Value by Restockability"
            ),
            color_discrete_map={
                "Restockable":
                    COLORS[
                        "uae_green"
                    ],
                "Non-Restockable":
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


# ============================================================
# Categories
# ============================================================

def _render_category_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Category Return Exposure",
        (
            "Categories ranked by returned value, "
            "units, lag and operational recoverability."
        ),
    )

    category = (
        _aggregate_returns(
            data,
            [
                "CategoryName"
            ],
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            category.sort_values(
                "ReturnedValue"
            ),
            x="ReturnedValue",
            y="CategoryName",
            orientation="h",
            color="RestockableLinePct",
            hover_data=[
                "ReturnedUnits",
                "AvgReturnLagDays",
                "RefundAmount",
            ],
            title=(
                "Returned Value by Category"
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
            category,
            x="ReturnedUnits",
            y="ReturnedValue",
            size="ReturnLines",
            color="AvgReturnLagDays",
            hover_name="CategoryName",
            title=(
                "Category Return Severity Matrix"
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


# ============================================================
# Product Risk
# ============================================================

def _render_product_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Product Return Risk",
        (
            "SKU-level return exposure and "
            "high-value product review."
        ),
    )

    products = (
        _aggregate_returns(
            data,
            [
                "ProductId",
                "SKU",
                "ProductName",
                "CategoryName",
                "BrandName",
            ],
        )
    )

    products[
        "RiskScore"
    ] = (
        _min_max(
            products[
                "ReturnedValue"
            ]
        )
        * .40
        + _min_max(
            products[
                "ReturnedUnits"
            ]
        )
        * .25
        + _min_max(
            products[
                "AvgReturnLagDays"
            ]
        )
        * .15
        + _min_max(
            products[
                "RefundAmount"
            ]
        )
        * .20
    )

    products[
        "RiskTier"
    ] = pd.cut(
        products[
            "RiskScore"
        ],
        bins=[
            -np.inf,
            35,
            60,
            80,
            np.inf,
        ],
        labels=[
            "Low",
            "Moderate",
            "High",
            "Critical",
        ],
    )

    count = min(
        25,
        len(products),
    )

    left, right = st.columns(2)

    with left:
        top = (
            products.nlargest(
                count,
                "ReturnedValue",
            )
            .sort_values(
                "ReturnedValue"
            )
        )

        figure = px.bar(
            top,
            x="ReturnedValue",
            y="SKU",
            orientation="h",
            color="RiskTier",
            hover_name="ProductName",
            hover_data=[
                "CategoryName",
                "BrandName",
                "ReturnedUnits",
                "AvgReturnLagDays",
                "RiskScore",
            ],
            title=(
                "Highest Returned Value SKUs"
            ),
            color_discrete_map={
                "Low":
                    COLORS[
                        "uae_green"
                    ],
                "Moderate":
                    COLORS["info"],
                "High":
                    COLORS["gold"],
                "Critical":
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                600,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            products,
            x="ReturnedUnits",
            y="ReturnedValue",
            size="ReturnLines",
            color="RiskTier",
            hover_name="ProductName",
            hover_data=[
                "SKU",
                "CategoryName",
                "RiskScore",
            ],
            title=(
                "Product Return Risk Matrix"
            ),
            color_discrete_map={
                "Low":
                    COLORS[
                        "uae_green"
                    ],
                "Moderate":
                    COLORS["info"],
                "High":
                    COLORS["gold"],
                "Critical":
                    COLORS[
                        "uae_red"
                    ],
            },
            opacity=.7,
        )

        st.plotly_chart(
            style_figure(
                figure,
                600,
            ),
            use_container_width=True,
        )

    st.caption(
        "Product Return Risk Score is a relative "
        "review-prioritization indicator, not a "
        "predicted probability of return."
    )


# ============================================================
# Store / Emirate Risk
# ============================================================

def _render_store_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Store & Emirate Return Exposure",
        (
            "Geographic concentration of returned "
            "value and operational return activity."
        ),
    )

    stores = (
        _aggregate_returns(
            data,
            [
                "StoreId",
                "StoreCode",
                "StoreName",
                "EmirateName",
            ],
        )
    )

    emirates = (
        _aggregate_returns(
            data,
            [
                "EmirateId",
                "EmirateName",
            ],
        )
    )

    left, right = st.columns(2)

    with left:
        top = (
            stores.nlargest(
                min(
                    20,
                    len(stores),
                ),
                "ReturnedValue",
            )
            .sort_values(
                "ReturnedValue"
            )
        )

        figure = px.bar(
            top,
            x="ReturnedValue",
            y="StoreCode",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "StoreName",
                "ReturnedUnits",
                "AvgReturnLagDays",
                "RestockableLinePct",
            ],
            title=(
                "Stores by Returned Value"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                520,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.bar(
            emirates.sort_values(
                "ReturnedValue"
            ),
            x="ReturnedValue",
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "ReturnedUnits",
                "RefundAmount",
                "AvgReturnLagDays",
            ],
            title=(
                "Returned Value by Emirate"
            ),
        )

        figure.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            style_figure(
                figure,
                520,
                legend=False,
            ),
            use_container_width=True,
        )


# ============================================================
# Pareto
# ============================================================

def _render_pareto(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Pareto Analysis",
        (
            "Identify the SKUs responsible for "
            "the majority of returned value."
        ),
    )

    products = (
        data.groupby(
            [
                "SKU",
                "ProductName",
            ],
            as_index=False,
        )
        .agg(
            ReturnedValue=(
                "ReturnedNetAmount",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnQuantity",
                "sum",
            ),
        )
        .sort_values(
            "ReturnedValue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    total = _safe_float(
        products[
            "ReturnedValue"
        ].sum()
    )

    products[
        "ValueSharePct"
    ] = (
        products[
            "ReturnedValue"
        ]
        / total
        * 100
        if total
        else 0
    )

    products[
        "CumulativeValuePct"
    ] = (
        products[
            "ReturnedValue"
        ]
        .cumsum()
        / total
        * 100
        if total
        else 0
    )

    top = products.head(
        min(
            60,
            len(products),
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=top["SKU"],
            y=top[
                "ReturnedValue"
            ],
            name="Returned Value",
            marker_color=(
                COLORS[
                    "uae_red"
                ]
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=top["SKU"],
            y=top[
                "CumulativeValuePct"
            ],
            name="Cumulative %",
            yaxis="y2",
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
            "SKU Return Value Pareto"
        ),
        yaxis_title=(
            "Returned Value"
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[
                0,
                105,
            ],
            title=(
                "Cumulative %"
            ),
            gridcolor=(
                "rgba(0,0,0,0)"
            ),
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            500,
        ),
        use_container_width=True,
    )


# ============================================================
# Anomalies
# ============================================================

def _render_anomalies(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Anomaly Screening",
        (
            "Statistical candidates based on unusually "
            "high returned value, quantity or lag."
        ),
    )

    anomalies = (
        data[
            data[
                "AnomalyCandidate"
            ]
        ]
        .sort_values(
            "ReturnedNetAmount",
            ascending=False,
        )
        .copy()
    )

    row = st.columns(4)

    metric(
        row[0],
        "Candidates",
        number(
            len(anomalies)
        ),
    )

    metric(
        row[1],
        "High Value",
        number(
            (
                data[
                    "ValueZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    metric(
        row[2],
        "High Quantity",
        number(
            (
                data[
                    "QuantityZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    metric(
        row[3],
        "Long Lag",
        number(
            (
                data[
                    "LagZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    figure = px.scatter(
        data,
        x="ReturnLagDays",
        y="ReturnedNetAmount",
        size="ReturnQuantity",
        color="AnomalyCandidate",
        hover_name="ProductName",
        hover_data=[
            "ReturnNumber",
            "SKU",
            "StoreCode",
            "ReturnReason",
            "ValueZScore",
            "LagZScore",
        ],
        title=(
            "Return Value / Lag "
            "Anomaly Matrix"
        ),
        color_discrete_map={
            True:
                COLORS[
                    "uae_red"
                ],
            False:
                COLORS[
                    "muted"
                ],
        },
        opacity=.65,
    )

    st.plotly_chart(
        style_figure(
            figure,
            470,
        ),
        use_container_width=True,
    )

    if not anomalies.empty:
        st.dataframe(
            anomalies[
                [
                    "ReturnNumber",
                    "ReturnDate",
                    "StoreCode",
                    "SKU",
                    "ProductName",
                    "ReturnReason",
                    "ReturnQuantity",
                    "ReturnedNetAmount",
                    "RefundAmount",
                    "ReturnLagDays",
                    "SeverityTier",
                    "ValueZScore",
                    "QuantityZScore",
                    "LagZScore",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Anomaly candidates are statistical screening "
        "signals and should not be interpreted as "
        "confirmed fraud or operational errors."
    )


# ============================================================
# Correlation
# ============================================================

def _render_correlation(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Return Correlation Diagnostics"
    )

    columns = [
        "ReturnQuantity",
        "ReturnedNetAmount",
        "RefundAmount",
        "ReturnedCOGS",
        "ReturnLagDays",
        "LineQuantityReturnPct",
        "RefundCoveragePct",
        "ReturnSeverity",
    ]

    available = [
        column
        for column in columns
        if column
        in data.columns
    ]

    correlation = (
        data[
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
            "Return KPI Correlation Matrix"
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
        "Correlation is descriptive and does not "
        "establish causal relationships."
    )


# ============================================================
# Data Explorer
# ============================================================

def _render_data_explorer(
    user,
    data: pd.DataFrame,
) -> None:
    section_header(
        "Returns Data Explorer",
        (
            "Secure filtered returns available "
            "for operational analysis and export."
        ),
    )

    (
        detail_tab,
        reason_tab,
        product_tab,
        store_tab,
    ) = st.tabs(
        [
            "Return Detail",
            "Reasons",
            "Products",
            "Stores",
        ]
    )

    with detail_tab:
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=data,
            label=(
                "Export filtered return detail"
            ),
            file_name=(
                "returns_filtered_detail.csv"
            ),
            key=(
                "returns_export_detail"
            ),
        )

    with reason_tab:
        reasons = (
            _aggregate_returns(
                data,
                [
                    "ReturnReason"
                ],
            )
        )

        st.dataframe(
            reasons,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=reasons,
            label=(
                "Export return reason summary"
            ),
            file_name=(
                "returns_reason_summary.csv"
            ),
            key=(
                "returns_export_reasons"
            ),
        )

    with product_tab:
        products = (
            _aggregate_returns(
                data,
                [
                    "SKU",
                    "ProductName",
                    "CategoryName",
                ],
            )
            .sort_values(
                "ReturnedValue",
                ascending=False,
            )
        )

        st.dataframe(
            products,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=products,
            label=(
                "Export product return summary"
            ),
            file_name=(
                "returns_product_summary.csv"
            ),
            key=(
                "returns_export_products"
            ),
        )

    with store_tab:
        stores = (
            _aggregate_returns(
                data,
                [
                    "StoreCode",
                    "StoreName",
                    "EmirateName",
                ],
            )
            .sort_values(
                "ReturnedValue",
                ascending=False,
            )
        )

        st.dataframe(
            stores,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=stores,
            label=(
                "Export store return summary"
            ),
            file_name=(
                "returns_store_summary.csv"
            ),
            key=(
                "returns_export_stores"
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
        "Returns Intelligence Command Center",
        (
            "Advanced post-sale intelligence covering "
            "return value, reasons, lag, refunds, "
            "restockability, merchandise exposure, "
            "geographic risk and anomaly screening."
        ),
        "UAE POST-SALE RISK INTELLIGENCE",
    )

    st.caption(
        "Reporting period is based on original sale date: "
        f"{_period_label(filters)}"
    )

    raw = get_filtered_returns(
        user,
        filters,
    )

    if raw.empty:
        st.warning(
            "No completed return records match "
            "the active analytical filters."
        )
        return

    data = _prepare_returns(
        raw
    )

    _render_kpis(
        data
    )

    _render_signals(
        data
    )

    _render_monthly_trend(
        data
    )

    _render_reason_analysis(
        data
    )

    _render_lag_analysis(
        data
    )

    _render_refund_analysis(
        data
    )

    _render_restockability(
        data
    )

    _render_category_analysis(
        data
    )

    _render_product_analysis(
        data
    )

    _render_store_analysis(
        data
    )

    _render_pareto(
        data
    )

    _render_anomalies(
        data
    )

    _render_correlation(
        data
    )

    _render_data_explorer(
        user,
        data,
    )