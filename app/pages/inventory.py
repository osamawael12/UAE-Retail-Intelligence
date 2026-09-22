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
    get_filtered_inventory,
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
        score = (
            100 - score
        )

    return score


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


# ============================================================
# Data Preparation
# ============================================================

def _prepare_inventory(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    data = dataframe.copy()

    if data.empty:
        return data

    data[
        "CurrentStock"
    ] = pd.to_numeric(
        data[
            "CurrentStock"
        ],
        errors="coerce",
    ).fillna(0)

    data[
        "ReorderPoint"
    ] = pd.to_numeric(
        data[
            "ReorderPoint"
        ],
        errors="coerce",
    ).fillna(0)

    data[
        "ReorderQuantity"
    ] = pd.to_numeric(
        data[
            "ReorderQuantity"
        ],
        errors="coerce",
    ).fillna(0)

    data[
        "InventoryValue"
    ] = pd.to_numeric(
        data[
            "InventoryValue"
        ],
        errors="coerce",
    ).fillna(0)

    data[
        "GrossUnitsSold"
    ] = pd.to_numeric(
        data[
            "GrossUnitsSold"
        ],
        errors="coerce",
    ).fillna(0)

    data[
        "DaysSinceLastSale"
    ] = pd.to_numeric(
        data[
            "DaysSinceLastSale"
        ],
        errors="coerce",
    )

    data[
        "StockToReorderRatio"
    ] = np.where(
        data[
            "ReorderPoint"
        ] > 0,
        data[
            "CurrentStock"
        ]
        / data[
            "ReorderPoint"
        ],
        np.nan,
    )

    data[
        "SalesToStockRatio"
    ] = np.where(
        data[
            "CurrentStock"
        ] > 0,
        data[
            "GrossUnitsSold"
        ]
        / data[
            "CurrentStock"
        ],
        np.nan,
    )

    data[
        "StockCoverageProxy"
    ] = np.where(
        data[
            "GrossUnitsSold"
        ] > 0,
        data[
            "CurrentStock"
        ]
        / data[
            "GrossUnitsSold"
        ],
        np.nan,
    )

    # --------------------------------------------------------
    # Inventory movement profile
    #
    # DaysSinceLastSale is the strongest recency signal
    # available in the existing inventory analytics view.
    # --------------------------------------------------------

    data[
        "MovementClass"
    ] = np.select(
        [
            data[
                "LastSaleDate"
            ].isna(),

            data[
                "DaysSinceLastSale"
            ]
            >= 180,

            data[
                "DaysSinceLastSale"
            ]
            >= 90,

            data[
                "DaysSinceLastSale"
            ]
            >= 45,

            data[
                "DaysSinceLastSale"
            ]
            >= 15,
        ],
        [
            "No Recorded Sale",
            "Dead / Dormant",
            "Very Slow",
            "Slow",
            "Moderate",
        ],
        default="Fast",
    )

    # --------------------------------------------------------
    # Capital risk
    # --------------------------------------------------------

    data[
        "CapitalRiskFlag"
    ] = np.select(
        [
            (
                data[
                    "MovementClass"
                ]
                .isin(
                    [
                        "No Recorded Sale",
                        "Dead / Dormant",
                    ]
                )
            )
            & (
                data[
                    "InventoryValue"
                ]
                >= data[
                    "InventoryValue"
                ].quantile(
                    .75
                )
            ),

            (
                data[
                    "MovementClass"
                ]
                .isin(
                    [
                        "Very Slow",
                        "Slow",
                    ]
                )
            )
            & (
                data[
                    "InventoryValue"
                ]
                >= data[
                    "InventoryValue"
                ].median()
            ),

            data[
                "StockStatus"
            ]
            == "STOCKOUT",

            data[
                "ReorderRisk"
            ]
            .isin(
                [
                    "CRITICAL",
                    "HIGH",
                ]
            ),
        ],
        [
            "High Dead-Stock Capital",
            "Slow-Moving Capital",
            "Stockout",
            "Reorder Exposure",
        ],
        default="Normal",
    )

    # --------------------------------------------------------
    # Risk Score
    # --------------------------------------------------------

    stock_shortage_score = (
        _min_max_score(
            (
                data[
                    "ReorderPoint"
                ]
                - data[
                    "CurrentStock"
                ]
            )
            .clip(
                lower=0
            )
        )
    )

    recency_score = (
        _min_max_score(
            data[
                "DaysSinceLastSale"
            ]
            .fillna(
                data[
                    "DaysSinceLastSale"
                ]
                .max()
                if data[
                    "DaysSinceLastSale"
                ]
                .notna()
                .any()
                else 0
            )
        )
    )

    capital_score = (
        _min_max_score(
            data[
                "InventoryValue"
            ]
        )
    )

    low_velocity_score = (
        _min_max_score(
            data[
                "GrossUnitsSold"
            ],
            reverse=True,
        )
    )

    data[
        "InventoryRiskScore"
    ] = (
        stock_shortage_score
        * .30
        + recency_score
        * .25
        + capital_score
        * .25
        + low_velocity_score
        * .20
    )

    data[
        "InventoryRiskScore"
    ] = (
        data[
            "InventoryRiskScore"
        ]
        .clip(
            0,
            100,
        )
    )

    data[
        "RiskTier"
    ] = pd.cut(
        data[
            "InventoryRiskScore"
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

    # --------------------------------------------------------
    # Inventory value concentration
    # --------------------------------------------------------

    data = (
        data.sort_values(
            "InventoryValue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    total_value = _safe_float(
        data[
            "InventoryValue"
        ].sum()
    )

    data[
        "InventoryValueSharePct"
    ] = (
        data[
            "InventoryValue"
        ]
        / total_value
        * 100
        if total_value
        else 0
    )

    data[
        "CumulativeInventoryValuePct"
    ] = (
        data[
            "InventoryValue"
        ]
        .cumsum()
        / total_value
        * 100
        if total_value
        else 0
    )

    previous_cumulative = (
        data[
            "CumulativeInventoryValuePct"
        ]
        - data[
            "InventoryValueSharePct"
        ]
    )

    data[
        "InventoryABCClass"
    ] = np.select(
        [
            previous_cumulative
            < 80,

            previous_cumulative
            < 95,
        ],
        [
            "A",
            "B",
        ],
        default="C",
    )

    # --------------------------------------------------------
    # Outlier screening
    # --------------------------------------------------------

    data[
        "InventoryValueZScore"
    ] = _zscore(
        data[
            "InventoryValue"
        ]
    )

    data[
        "StockZScore"
    ] = _zscore(
        data[
            "CurrentStock"
        ]
    )

    data[
        "DaysSinceSaleZScore"
    ] = _zscore(
        data[
            "DaysSinceLastSale"
        ]
    )

    data[
        "OutlierCandidate"
    ] = (
        (
            data[
                "InventoryValueZScore"
            ]
            >= 2.5
        )
        | (
            data[
                "StockZScore"
            ]
            >= 2.5
        )
        | (
            data[
                "DaysSinceSaleZScore"
            ]
            >= 2.5
        )
    )

    return data


# ============================================================
# Aggregations
# ============================================================

def _aggregate_inventory(
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
            Records=(
                "ProductId",
                "count",
            ),

            Products=(
                "ProductId",
                "nunique",
            ),

            CurrentStock=(
                "CurrentStock",
                "sum",
            ),

            ReorderPoint=(
                "ReorderPoint",
                "sum",
            ),

            ReorderQuantity=(
                "ReorderQuantity",
                "sum",
            ),

            InventoryValue=(
                "InventoryValue",
                "sum",
            ),

            GrossUnitsSold=(
                "GrossUnitsSold",
                "sum",
            ),

            AvgDaysSinceLastSale=(
                "DaysSinceLastSale",
                "mean",
            ),

            AvgRiskScore=(
                "InventoryRiskScore",
                "mean",
            ),
        )
    )

    summary[
        "SalesToStockRatio"
    ] = np.where(
        summary[
            "CurrentStock"
        ] > 0,
        summary[
            "GrossUnitsSold"
        ]
        / summary[
            "CurrentStock"
        ],
        np.nan,
    )

    return summary


# ============================================================
# KPI Section
# ============================================================

def _render_kpis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory KPI Pulse",
        (
            "Current inventory position under "
            "the authenticated geography scope."
        ),
    )

    total_value = _safe_float(
        data[
            "InventoryValue"
        ].sum()
    )

    current_stock = _safe_float(
        data[
            "CurrentStock"
        ].sum()
    )

    stockouts = int(
        data[
            "StockStatus"
        ]
        .eq("STOCKOUT")
        .sum()
    )

    low_stock = int(
        data[
            "StockStatus"
        ]
        .eq("LOW_STOCK")
        .sum()
    )

    critical_high = int(
        data[
            "ReorderRisk"
        ]
        .isin(
            [
                "CRITICAL",
                "HIGH",
            ]
        )
        .sum()
    )

    slow_moving = int(
        data[
            "MovementClass"
        ]
        .isin(
            [
                "Slow",
                "Very Slow",
                "Dead / Dormant",
                "No Recorded Sale",
            ]
        )
        .sum()
    )

    dead_value = _safe_float(
        data.loc[
            data[
                "MovementClass"
            ]
            .isin(
                [
                    "Dead / Dormant",
                    "No Recorded Sale",
                ]
            ),
            "InventoryValue",
        ].sum()
    )

    avg_risk = _safe_float(
        data[
            "InventoryRiskScore"
        ].mean()
    )

    row = st.columns(4)

    metric(
        row[0],
        "Inventory Value",
        money(
            total_value
        ),
    )

    metric(
        row[1],
        "Current Stock Units",
        number(
            current_stock
        ),
    )

    metric(
        row[2],
        "Store / Product Records",
        number(
            len(data)
        ),
    )

    metric(
        row[3],
        "Products",
        number(
            data[
                "ProductId"
            ].nunique()
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Stockouts",
        number(
            stockouts
        ),
    )

    metric(
        row[1],
        "Low Stock",
        number(
            low_stock
        ),
    )

    metric(
        row[2],
        "High / Critical Reorder",
        number(
            critical_high
        ),
    )

    metric(
        row[3],
        "Slow / Dormant Records",
        number(
            slow_moving
        ),
    )

    row = st.columns(2)

    metric(
        row[0],
        "Dead / Dormant Capital",
        money(
            dead_value
        ),
    )

    metric(
        row[1],
        "Average Inventory Risk",
        f"{avg_risk:.1f}/100",
    )


# ============================================================
# Signals
# ============================================================

def _render_signals(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Management Signals"
    )

    highest_value = (
        data.sort_values(
            "InventoryValue",
            ascending=False,
        )
        .iloc[0]
    )

    highest_risk = (
        data.sort_values(
            "InventoryRiskScore",
            ascending=False,
        )
        .iloc[0]
    )

    slow_value = _safe_float(
        data.loc[
            data[
                "MovementClass"
            ]
            .isin(
                [
                    "Slow",
                    "Very Slow",
                    "Dead / Dormant",
                    "No Recorded Sale",
                ]
            ),
            "InventoryValue",
        ].sum()
    )

    total_value = _safe_float(
        data[
            "InventoryValue"
        ].sum()
    )

    slow_share = (
        slow_value
        / total_value
        * 100
        if total_value
        else 0
    )

    reorder_candidates = int(
        data[
            "ReorderRisk"
        ]
        .isin(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
            ]
        )
        .sum()
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "HIGHEST CAPITAL RECORD",
            (
                f"{highest_value['StoreCode']} / "
                f"{highest_value['SKU']}"
            ),
            money(
                highest_value[
                    "InventoryValue"
                ]
            ),
            "gold",
        )

    with columns[1]:
        insight_card(
            "HIGHEST RISK RECORD",
            (
                f"{highest_risk['StoreCode']} / "
                f"{highest_risk['SKU']}"
            ),
            (
                f"{_safe_float(highest_risk['InventoryRiskScore']):.1f}/100"
            ),
            "red",
        )

    with columns[2]:
        insight_card(
            "SLOW CAPITAL SHARE",
            percentage(
                slow_share
            ),
            (
                "Inventory value tied to "
                "slow or dormant records."
            ),
            (
                "red"
                if slow_share >= 40
                else "gold"
                if slow_share >= 20
                else "green"
            ),
        )

    with columns[3]:
        insight_card(
            "REORDER CANDIDATES",
            number(
                reorder_candidates
            ),
            (
                "Medium, high or critical "
                "reorder-risk records."
            ),
            (
                "red"
                if reorder_candidates
                else "green"
            ),
        )


# ============================================================
# Stock Health
# ============================================================

def _render_stock_health(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Stock Health",
        (
            "Current stock status and "
            "reorder-risk distribution."
        ),
    )

    status = (
        data.groupby(
            "StockStatus",
            as_index=False,
        )
        .agg(
            Records=(
                "ProductId",
                "count",
            ),
            InventoryValue=(
                "InventoryValue",
                "sum",
            ),
            CurrentStock=(
                "CurrentStock",
                "sum",
            ),
        )
    )

    risk = (
        data.groupby(
            "ReorderRisk",
            as_index=False,
        )
        .agg(
            Records=(
                "ProductId",
                "count",
            ),
            InventoryValue=(
                "InventoryValue",
                "sum",
            ),
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.pie(
            status,
            names="StockStatus",
            values="Records",
            hole=.62,
            color="StockStatus",
            title=(
                "Stock Status Mix"
            ),
            color_discrete_map={
                "HEALTHY":
                    COLORS[
                        "uae_green"
                    ],
                "LOW_STOCK":
                    COLORS["gold"],
                "STOCKOUT":
                    COLORS[
                        "uae_red"
                    ],
            },
            hover_data=[
                "InventoryValue",
                "CurrentStock",
            ],
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
            ),
            use_container_width=True,
        )

    with right:
        risk_order = [
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ]

        figure = px.bar(
            risk,
            x="ReorderRisk",
            y="Records",
            color="ReorderRisk",
            hover_data=[
                "InventoryValue"
            ],
            title=(
                "Reorder Risk Profile"
            ),
            category_orders={
                "ReorderRisk":
                    risk_order
            },
            color_discrete_map={
                "LOW":
                    COLORS[
                        "uae_green"
                    ],
                "MEDIUM":
                    COLORS["gold"],
                "HIGH":
                    "#E88A32",
                "CRITICAL":
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                430,
                legend=False,
            ),
            use_container_width=True,
        )


# ============================================================
# Capital Allocation
# ============================================================

def _render_category_capital(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Capital Allocation",
        (
            "Inventory value, stock and "
            "sales velocity by category."
        ),
    )

    category = (
        _aggregate_inventory(
            data,
            [
                "CategoryName"
            ],
        )
    )

    total = _safe_float(
        category[
            "InventoryValue"
        ].sum()
    )

    category[
        "InventoryValueSharePct"
    ] = (
        category[
            "InventoryValue"
        ]
        / total
        * 100
        if total
        else 0
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            category.sort_values(
                "InventoryValue"
            ),
            x="InventoryValue",
            y="CategoryName",
            orientation="h",
            color="InventoryValueSharePct",
            hover_data=[
                "Products",
                "CurrentStock",
                "GrossUnitsSold",
                "AvgDaysSinceLastSale",
            ],
            title=(
                "Inventory Value by Category"
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
            x="GrossUnitsSold",
            y="InventoryValue",
            size="CurrentStock",
            color="AvgRiskScore",
            hover_name="CategoryName",
            hover_data=[
                "Products",
                "SalesToStockRatio",
            ],
            title=(
                "Category Capital / "
                "Sales Velocity Matrix"
            ),
            color_continuous_scale=(
                "RdYlGn_r"
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
# Movement / Slow Stock
# ============================================================

def _render_movement_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Movement Intelligence",
        (
            "Last-sale recency and capital "
            "exposure across movement classes."
        ),
    )

    movement = (
        data.groupby(
            "MovementClass",
            as_index=False,
        )
        .agg(
            Records=(
                "ProductId",
                "count",
            ),
            InventoryValue=(
                "InventoryValue",
                "sum",
            ),
            CurrentStock=(
                "CurrentStock",
                "sum",
            ),
            GrossUnitsSold=(
                "GrossUnitsSold",
                "sum",
            ),
        )
    )

    movement_order = [
        "Fast",
        "Moderate",
        "Slow",
        "Very Slow",
        "Dead / Dormant",
        "No Recorded Sale",
    ]

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            movement,
            x="MovementClass",
            y="InventoryValue",
            color="MovementClass",
            hover_data=[
                "Records",
                "CurrentStock",
                "GrossUnitsSold",
            ],
            category_orders={
                "MovementClass":
                    movement_order
            },
            title=(
                "Inventory Value by "
                "Movement Class"
            ),
            color_discrete_map={
                "Fast":
                    COLORS[
                        "uae_green"
                    ],
                "Moderate":
                    COLORS["info"],
                "Slow":
                    COLORS["gold"],
                "Very Slow":
                    "#E88A32",
                "Dead / Dormant":
                    COLORS[
                        "uae_red"
                    ],
                "No Recorded Sale":
                    "#8B1E2D",
            },
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
        figure = px.pie(
            movement,
            names="MovementClass",
            values="InventoryValue",
            hole=.58,
            title=(
                "Capital Mix by Movement Class"
            ),
            color="MovementClass",
            color_discrete_map={
                "Fast":
                    COLORS[
                        "uae_green"
                    ],
                "Moderate":
                    COLORS["info"],
                "Slow":
                    COLORS["gold"],
                "Very Slow":
                    "#E88A32",
                "Dead / Dormant":
                    COLORS[
                        "uae_red"
                    ],
                "No Recorded Sale":
                    "#8B1E2D",
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    slow = (
        data[
            data[
                "MovementClass"
            ]
            .isin(
                [
                    "Slow",
                    "Very Slow",
                    "Dead / Dormant",
                    "No Recorded Sale",
                ]
            )
        ]
        .copy()
    )

    if not slow.empty:
        figure = px.scatter(
            slow,
            x="DaysSinceLastSale",
            y="InventoryValue",
            size="CurrentStock",
            color="MovementClass",
            hover_name="ProductName",
            hover_data=[
                "SKU",
                "StoreCode",
                "CategoryName",
                "ReorderRisk",
                "GrossUnitsSold",
            ],
            title=(
                "Slow-Moving Capital Exposure"
            ),
            color_discrete_map={
                "Slow":
                    COLORS["gold"],
                "Very Slow":
                    "#E88A32",
                "Dead / Dormant":
                    COLORS[
                        "uae_red"
                    ],
                "No Recorded Sale":
                    "#8B1E2D",
            },
            opacity=.72,
        )

        st.plotly_chart(
            style_figure(
                figure,
                500,
            ),
            use_container_width=True,
        )


# ============================================================
# Dead Stock
# ============================================================

def _render_dead_stock(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Dead / Dormant Stock Candidates",
        (
            "High-recency or no-sale inventory "
            "with capital still tied in stock."
        ),
    )

    dead = (
        data[
            data[
                "MovementClass"
            ]
            .isin(
                [
                    "Dead / Dormant",
                    "No Recorded Sale",
                ]
            )
        ]
        .sort_values(
            "InventoryValue",
            ascending=False,
        )
        .copy()
    )

    dead_value = _safe_float(
        dead[
            "InventoryValue"
        ].sum()
    )

    dead_units = _safe_float(
        dead[
            "CurrentStock"
        ].sum()
    )

    row = st.columns(3)

    metric(
        row[0],
        "Dead / Dormant Records",
        number(
            len(dead)
        ),
    )

    metric(
        row[1],
        "Capital Exposure",
        money(
            dead_value
        ),
    )

    metric(
        row[2],
        "Stock Units",
        number(
            dead_units
        ),
    )

    if dead.empty:
        st.success(
            "No dead or dormant stock "
            "candidates under current rules."
        )
        return

    top = dead.head(
        min(
            30,
            len(dead),
        )
    )

    figure = px.bar(
        top.sort_values(
            "InventoryValue"
        ),
        x="InventoryValue",
        y="SKU",
        orientation="h",
        color="MovementClass",
        hover_name="ProductName",
        hover_data=[
            "StoreCode",
            "CategoryName",
            "CurrentStock",
            "DaysSinceLastSale",
        ],
        title=(
            "Highest Dead / Dormant "
            "Capital Records"
        ),
        color_discrete_map={
            "Dead / Dormant":
                COLORS[
                    "uae_red"
                ],
            "No Recorded Sale":
                "#8B1E2D",
        },
    )

    st.plotly_chart(
        style_figure(
            figure,
            650,
        ),
        use_container_width=True,
    )


# ============================================================
# Reorder
# ============================================================

def _render_reorder_analysis(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Reorder Control",
        (
            "Stock positions at or below reorder "
            "thresholds and operational priority."
        ),
    )

    candidates = (
        data[
            data[
                "ReorderRisk"
            ]
            .isin(
                [
                    "CRITICAL",
                    "HIGH",
                    "MEDIUM",
                ]
            )
        ]
        .copy()
    )

    if candidates.empty:
        st.success(
            "No medium/high/critical reorder "
            "candidates under the active scope."
        )
        return

    priority_order = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
    }

    candidates[
        "RiskOrder"
    ] = (
        candidates[
            "ReorderRisk"
        ]
        .map(
            priority_order
        )
    )

    candidates = (
        candidates.sort_values(
            [
                "RiskOrder",
                "InventoryRiskScore",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    left, right = st.columns(2)

    with left:
        risk_summary = (
            candidates.groupby(
                "ReorderRisk",
                as_index=False,
            )
            .agg(
                Records=(
                    "ProductId",
                    "count",
                ),
                SuggestedUnits=(
                    "ReorderQuantity",
                    "sum",
                ),
                InventoryValue=(
                    "InventoryValue",
                    "sum",
                ),
            )
        )

        figure = px.bar(
            risk_summary,
            x="ReorderRisk",
            y="Records",
            color="ReorderRisk",
            hover_data=[
                "SuggestedUnits",
                "InventoryValue",
            ],
            title=(
                "Reorder Candidates by Risk"
            ),
            category_orders={
                "ReorderRisk": [
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL",
                ]
            },
            color_discrete_map={
                "MEDIUM":
                    COLORS["gold"],
                "HIGH":
                    "#E88A32",
                "CRITICAL":
                    COLORS[
                        "uae_red"
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

    with right:
        figure = px.scatter(
            candidates,
            x="CurrentStock",
            y="GrossUnitsSold",
            size="ReorderQuantity",
            color="ReorderRisk",
            hover_name="ProductName",
            hover_data=[
                "StoreCode",
                "SKU",
                "ReorderPoint",
                "InventoryRiskScore",
            ],
            title=(
                "Stock vs Historical Sales "
                "for Reorder Candidates"
            ),
            color_discrete_map={
                "MEDIUM":
                    COLORS["gold"],
                "HIGH":
                    "#E88A32",
                "CRITICAL":
                    COLORS[
                        "uae_red"
                    ],
            },
        )

        st.plotly_chart(
            style_figure(
                figure,
                420,
            ),
            use_container_width=True,
        )

    st.dataframe(
        candidates[
            [
                "StoreCode",
                "SKU",
                "ProductName",
                "CategoryName",
                "CurrentStock",
                "ReorderPoint",
                "ReorderQuantity",
                "StockStatus",
                "ReorderRisk",
                "GrossUnitsSold",
                "DaysSinceLastSale",
                "InventoryValue",
                "InventoryRiskScore",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Inventory ABC
# ============================================================

def _render_inventory_pareto(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Capital ABC / Pareto",
        (
            "Concentration of inventory value "
            "across store-product records."
        ),
    )

    top = data.head(
        min(
            75,
            len(data),
        )
    )

    labels = (
        top[
            "StoreCode"
        ].astype(str)
        + " / "
        + top[
            "SKU"
        ].astype(str)
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=top[
                "InventoryValue"
            ],
            name="Inventory Value",
            marker_color=(
                COLORS[
                    "uae_green"
                ]
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=labels,
            y=top[
                "CumulativeInventoryValuePct"
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
            "Inventory Value Pareto"
        ),
        yaxis_title=(
            "Inventory Value"
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[
                0,
                105,
            ],
            title=(
                "Cumulative Value %"
            ),
            gridcolor=(
                "rgba(0,0,0,0)"
            ),
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            510,
        ),
        use_container_width=True,
    )

    abc = (
        data.groupby(
            "InventoryABCClass",
            as_index=False,
        )
        .agg(
            Records=(
                "ProductId",
                "count",
            ),
            InventoryValue=(
                "InventoryValue",
                "sum",
            ),
            CurrentStock=(
                "CurrentStock",
                "sum",
            ),
        )
    )

    total = _safe_float(
        abc[
            "InventoryValue"
        ].sum()
    )

    abc[
        "ValueSharePct"
    ] = (
        abc[
            "InventoryValue"
        ]
        / total
        * 100
        if total
        else 0
    )

    figure = px.bar(
        abc,
        x="InventoryABCClass",
        y="InventoryValue",
        color="InventoryABCClass",
        text="ValueSharePct",
        hover_data=[
            "Records",
            "CurrentStock",
        ],
        title=(
            "Inventory Capital by ABC Class"
        ),
        color_discrete_map={
            "A":
                COLORS[
                    "uae_green"
                ],
            "B":
                COLORS["gold"],
            "C":
                COLORS[
                    "uae_red"
                ],
        },
    )

    figure.update_traces(
        texttemplate=(
            "%{text:.1f}%"
        )
    )

    st.plotly_chart(
        style_figure(
            figure,
            400,
            legend=False,
        ),
        use_container_width=True,
    )


# ============================================================
# Geography
# ============================================================

def _render_geography(
    data: pd.DataFrame,
) -> None:
    section_header(
        "UAE Inventory Geography",
        (
            "Inventory capital and operational "
            "risk across stores and emirates."
        ),
    )

    emirates = (
        _aggregate_inventory(
            data,
            [
                "EmirateId",
                "EmirateName",
            ],
        )
    )

    stores = (
        _aggregate_inventory(
            data,
            [
                "StoreId",
                "StoreCode",
                "StoreName",
                "EmirateName",
            ],
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            emirates.sort_values(
                "InventoryValue"
            ),
            x="InventoryValue",
            y="EmirateName",
            orientation="h",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_data=[
                "CurrentStock",
                "GrossUnitsSold",
                "AvgRiskScore",
            ],
            title=(
                "Inventory Value by Emirate"
            ),
        )

        figure.update_layout(
            showlegend=False,
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
            stores,
            x="InventoryValue",
            y="AvgRiskScore",
            size="CurrentStock",
            color="EmirateName",
            color_discrete_map=(
                EMIRATE_COLORS
            ),
            hover_name="StoreName",
            hover_data=[
                "StoreCode",
                "GrossUnitsSold",
                "SalesToStockRatio",
            ],
            title=(
                "Store Inventory Value / "
                "Risk Matrix"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                440,
            ),
            use_container_width=True,
        )

    top_stores = (
        stores.nlargest(
            min(
                20,
                len(stores),
            ),
            "InventoryValue",
        )
        .sort_values(
            "InventoryValue"
        )
    )

    figure = px.bar(
        top_stores,
        x="InventoryValue",
        y="StoreCode",
        orientation="h",
        color="EmirateName",
        color_discrete_map=(
            EMIRATE_COLORS
        ),
        hover_data=[
            "StoreName",
            "CurrentStock",
            "AvgRiskScore",
        ],
        title=(
            "Store Inventory Capital Ranking"
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
# Risk Scoring
# ============================================================

def _render_risk_score(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Risk Scoring",
        (
            "Relative prioritization based on "
            "stock shortage, sales recency, "
            "capital exposure and low velocity."
        ),
    )

    top = (
        data.nlargest(
            min(
                40,
                len(data),
            ),
            "InventoryRiskScore",
        )
        .sort_values(
            "InventoryRiskScore"
        )
    )

    figure = px.bar(
        top,
        x="InventoryRiskScore",
        y=(
            top[
                "StoreCode"
            ].astype(str)
            + " / "
            + top[
                "SKU"
            ].astype(str)
        ),
        orientation="h",
        color="RiskTier",
        hover_name="ProductName",
        hover_data=[
            "CategoryName",
            "CurrentStock",
            "ReorderPoint",
            "InventoryValue",
            "DaysSinceLastSale",
            "CapitalRiskFlag",
        ],
        title=(
            "Highest Inventory Risk Records"
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
            760,
        ),
        use_container_width=True,
    )

    st.caption(
        "Inventory Risk Score is a relative operational "
        "prioritization metric, not a probability of "
        "stockout or financial loss."
    )


# ============================================================
# Outliers
# ============================================================

def _render_outliers(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Outlier Screening",
        (
            "Statistical review candidates for "
            "unusually high value, stock or "
            "days since last sale."
        ),
    )

    candidates = (
        data[
            data[
                "OutlierCandidate"
            ]
        ]
        .copy()
    )

    row = st.columns(3)

    metric(
        row[0],
        "Value Outliers",
        number(
            (
                data[
                    "InventoryValueZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    metric(
        row[1],
        "Stock Outliers",
        number(
            (
                data[
                    "StockZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    metric(
        row[2],
        "Recency Outliers",
        number(
            (
                data[
                    "DaysSinceSaleZScore"
                ]
                >= 2.5
            ).sum()
        ),
    )

    if candidates.empty:
        st.success(
            "No records exceed the current "
            "outlier screening threshold."
        )
        return

    st.dataframe(
        candidates[
            [
                "StoreCode",
                "SKU",
                "ProductName",
                "CategoryName",
                "CurrentStock",
                "InventoryValue",
                "DaysSinceLastSale",
                "StockStatus",
                "ReorderRisk",
                "InventoryRiskScore",
                "InventoryValueZScore",
                "StockZScore",
                "DaysSinceSaleZScore",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Outliers are statistical review candidates, "
        "not confirmed inventory problems."
    )


# ============================================================
# Action Queue
# ============================================================

def _render_action_queue(
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Action Queue",
        (
            "Rule-based priorities for stockout, "
            "reorder and slow-capital review."
        ),
    )

    flags = (
        data.groupby(
            "CapitalRiskFlag",
            as_index=False,
        )
        .agg(
            Records=(
                "ProductId",
                "count",
            ),
            InventoryValue=(
                "InventoryValue",
                "sum",
            ),
            CurrentStock=(
                "CurrentStock",
                "sum",
            ),
            AvgRiskScore=(
                "InventoryRiskScore",
                "mean",
            ),
        )
    )

    figure = px.bar(
        flags.sort_values(
            "InventoryValue"
        ),
        x="InventoryValue",
        y="CapitalRiskFlag",
        orientation="h",
        color="CapitalRiskFlag",
        text="Records",
        hover_data=[
            "CurrentStock",
            "AvgRiskScore",
        ],
        title=(
            "Inventory Capital by Action Flag"
        ),
        color_discrete_map={
            "Normal":
                COLORS[
                    "uae_green"
                ],
            "Reorder Exposure":
                COLORS["gold"],
            "Stockout":
                COLORS[
                    "uae_red"
                ],
            "Slow-Moving Capital":
                "#E88A32",
            "High Dead-Stock Capital":
                "#8B1E2D",
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
        data[
            data[
                "CapitalRiskFlag"
            ]
            != "Normal"
        ]
        .sort_values(
            [
                "InventoryRiskScore",
                "InventoryValue",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .copy()
    )

    if not priority.empty:
        st.dataframe(
            priority[
                [
                    "StoreCode",
                    "SKU",
                    "ProductName",
                    "CategoryName",
                    "CurrentStock",
                    "ReorderPoint",
                    "ReorderQuantity",
                    "GrossUnitsSold",
                    "DaysSinceLastSale",
                    "InventoryValue",
                    "MovementClass",
                    "ReorderRisk",
                    "RiskTier",
                    "InventoryRiskScore",
                    "CapitalRiskFlag",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Data Explorer
# ============================================================

def _render_data_explorer(
    user,
    data: pd.DataFrame,
) -> None:
    section_header(
        "Inventory Data Explorer",
        (
            "Secure geography-filtered inventory "
            "datasets and action queues."
        ),
    )

    (
        detail_tab,
        reorder_tab,
        slow_tab,
        risk_tab,
    ) = st.tabs(
        [
            "Inventory Detail",
            "Reorder Candidates",
            "Slow / Dead Stock",
            "Risk Queue",
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
                "Export filtered inventory"
            ),
            file_name=(
                "inventory_filtered.csv"
            ),
            key=(
                "inventory_export_detail"
            ),
        )

    with reorder_tab:
        reorder = (
            data[
                data[
                    "ReorderRisk"
                ]
                .isin(
                    [
                        "CRITICAL",
                        "HIGH",
                        "MEDIUM",
                    ]
                )
            ]
            .copy()
        )

        st.dataframe(
            reorder,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=reorder,
            label=(
                "Export reorder candidates"
            ),
            file_name=(
                "inventory_reorder_candidates.csv"
            ),
            key=(
                "inventory_export_reorder"
            ),
        )

    with slow_tab:
        slow = (
            data[
                data[
                    "MovementClass"
                ]
                .isin(
                    [
                        "Slow",
                        "Very Slow",
                        "Dead / Dormant",
                        "No Recorded Sale",
                    ]
                )
            ]
            .copy()
        )

        st.dataframe(
            slow,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=slow,
            label=(
                "Export slow-moving inventory"
            ),
            file_name=(
                "inventory_slow_moving.csv"
            ),
            key=(
                "inventory_export_slow"
            ),
        )

    with risk_tab:
        risk = (
            data[
                data[
                    "CapitalRiskFlag"
                ]
                != "Normal"
            ]
            .copy()
        )

        st.dataframe(
            risk,
            use_container_width=True,
            hide_index=True,
        )

        secure_csv_download(
            user=user,
            dataframe=risk,
            label=(
                "Export inventory action queue"
            ),
            file_name=(
                "inventory_action_queue.csv"
            ),
            key=(
                "inventory_export_risk"
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
        "Inventory Control Tower",
        (
            "Advanced inventory intelligence covering "
            "capital exposure, stock health, reorder risk, "
            "movement velocity, dead-stock candidates, "
            "ABC concentration and operational priorities."
        ),
        "UAE INVENTORY INTELLIGENCE",
    )

    if (
        filters.start_date is not None
        or filters.end_date is not None
    ):
        st.info(
            "Inventory is a current snapshot. "
            "The Date filter is intentionally not applied "
            "to snapshot stock values. Emirate and Store "
            "filters remain active and RLS-secured."
        )

    raw = get_filtered_inventory(
        user,
        filters,
    )

    if raw.empty:
        st.warning(
            "No inventory records match the "
            "active geography filters."
        )
        return

    data = _prepare_inventory(
        raw
    )

    _render_kpis(
        data
    )

    _render_signals(
        data
    )

    _render_stock_health(
        data
    )

    _render_category_capital(
        data
    )

    _render_movement_analysis(
        data
    )

    _render_dead_stock(
        data
    )

    _render_reorder_analysis(
        data
    )

    _render_inventory_pareto(
        data
    )

    _render_geography(
        data
    )

    _render_risk_score(
        data
    )

    _render_outliers(
        data
    )

    _render_action_queue(
        data
    )

    _render_data_explorer(
        user,
        data,
    )