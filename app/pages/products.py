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
    get_filtered_product_performance,
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
        result = pd.Series(
            np.full(
                len(values),
                50.0,
            ),
            index=values.index,
        )

    else:
        result = (
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
        result = (
            100 - result
        )

    return result


def _weighted_average(
    dataframe: pd.DataFrame,
    value_column: str,
    weight_column: str,
) -> float:
    if dataframe.empty:
        return 0.0

    weights = pd.to_numeric(
        dataframe[
            weight_column
        ],
        errors="coerce",
    ).fillna(0)

    values = pd.to_numeric(
        dataframe[
            value_column
        ],
        errors="coerce",
    ).fillna(0)

    weight_sum = _safe_float(
        weights.sum()
    )

    if weight_sum == 0:
        return _safe_float(
            values.mean()
        )

    return _safe_float(
        np.average(
            values,
            weights=weights,
        )
    )


# ============================================================
# Product Preparation
# ============================================================

def _prepare_products(
    products: pd.DataFrame,
) -> pd.DataFrame:
    data = products.copy()

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

    total_units = _safe_float(
        data[
            "NetUnits"
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
        "UnitSharePct"
    ] = (
        data[
            "NetUnits"
        ]
        / total_units
        * 100
        if total_units
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

    previous_cumulative = (
        data[
            "CumulativeRevenuePct"
        ]
        - data[
            "RevenueSharePct"
        ]
    )

    data[
        "ABCClass"
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

    data[
        "RevenuePerOrder"
    ] = np.where(
        data[
            "Orders"
        ] != 0,
        data[
            "Revenue"
        ]
        / data[
            "Orders"
        ],
        0,
    )

    data[
        "UnitsPerOrder"
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
        "ProfitPerUnit"
    ] = np.where(
        data[
            "NetUnits"
        ] != 0,
        data[
            "GrossProfit"
        ]
        / data[
            "NetUnits"
        ],
        0,
    )

    data[
        "RevenuePerUnit"
    ] = np.where(
        data[
            "NetUnits"
        ] != 0,
        data[
            "Revenue"
        ]
        / data[
            "NetUnits"
        ],
        0,
    )

    data[
        "DiscountAmountPct"
    ] = np.where(
        data[
            "GrossSales"
        ] != 0,
        data[
            "DiscountAmount"
        ]
        * 100
        / data[
            "GrossSales"
        ],
        0,
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

    velocity_score = (
        _min_max_score(
            data[
                "NetUnits"
            ]
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

    discount_health_score = (
        _min_max_score(
            data[
                "DiscountDependencyPct"
            ],
            reverse=True,
        )
    )

    data[
        "ProductScore"
    ] = (
        revenue_score
        * .25
        + profit_score
        * .25
        + margin_score
        * .15
        + velocity_score
        * .15
        + return_health_score
        * .10
        + discount_health_score
        * .10
    )

    data[
        "ProductScore"
    ] = (
        data[
            "ProductScore"
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
            "ProductScore"
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

    revenue_median = (
        data[
            "Revenue"
        ].median()
    )

    margin_median = (
        data[
            "GrossMarginPct"
        ].median()
    )

    data[
        "PortfolioQuadrant"
    ] = np.select(
        [
            (
                data[
                    "Revenue"
                ]
                >= revenue_median
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                >= margin_median
            ),

            (
                data[
                    "Revenue"
                ]
                >= revenue_median
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                < margin_median
            ),

            (
                data[
                    "Revenue"
                ]
                < revenue_median
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                >= margin_median
            ),
        ],
        [
            "Revenue & Margin Leaders",
            "High Revenue / Margin Pressure",
            "Niche Margin Performers",
        ],
        default="Portfolio Review",
    )

    high_returns = (
        data[
            "ReturnRatePct"
        ].quantile(
            .75
        )
    )

    high_discount = (
        data[
            "DiscountDependencyPct"
        ].quantile(
            .75
        )
    )

    low_margin = (
        data[
            "GrossMarginPct"
        ].quantile(
            .25
        )
    )

    high_revenue = (
        data[
            "Revenue"
        ].quantile(
            .75
        )
    )

    data[
        "BusinessFlag"
    ] = np.select(
        [
            (
                data[
                    "ReturnRatePct"
                ]
                >= high_returns
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                <= low_margin
            ),

            (
                data[
                    "DiscountDependencyPct"
                ]
                >= high_discount
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                <= low_margin
            ),

            (
                data[
                    "Revenue"
                ]
                >= high_revenue
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                <= low_margin
            ),

            (
                data[
                    "Revenue"
                ]
                >= high_revenue
            )
            & (
                data[
                    "GrossMarginPct"
                ]
                > low_margin
            ),
        ],
        [
            "High Return / Low Margin",
            "Discount Dependency / Margin Risk",
            "High Revenue / Margin Pressure",
            "High Value Product",
        ],
        default="Normal",
    )

    data[
        "RevenueZScore"
    ] = _zscore(
        data["Revenue"]
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
        "DiscountZScore"
    ] = _zscore(
        data[
            "DiscountDependencyPct"
        ]
    )

    return data


# ============================================================
# Aggregation
# ============================================================

def _aggregate_dimension(
    products: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    summary = (
        products.groupby(
            group_columns,
            as_index=False,
        )
        .agg(
            Products=(
                "ProductId",
                "nunique",
            ),

            Orders=(
                "Orders",
                "sum",
            ),

            GrossUnits=(
                "GrossUnits",
                "sum",
            ),

            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),

            NetUnits=(
                "NetUnits",
                "sum",
            ),

            GrossSales=(
                "GrossSales",
                "sum",
            ),

            DiscountAmount=(
                "DiscountAmount",
                "sum",
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

    summary[
        "GrossMarginPct"
    ] = np.where(
        summary[
            "Revenue"
        ] != 0,
        summary[
            "GrossProfit"
        ]
        * 100
        / summary[
            "Revenue"
        ],
        0,
    )

    summary[
        "ReturnRatePct"
    ] = np.where(
        summary[
            "GrossUnits"
        ] != 0,
        summary[
            "ReturnedUnits"
        ]
        * 100
        / summary[
            "GrossUnits"
        ],
        0,
    )

    summary[
        "DiscountRatePct"
    ] = np.where(
        summary[
            "GrossSales"
        ] != 0,
        summary[
            "DiscountAmount"
        ]
        * 100
        / summary[
            "GrossSales"
        ],
        0,
    )

    summary[
        "RevenuePerProduct"
    ] = np.where(
        summary[
            "Products"
        ] != 0,
        summary[
            "Revenue"
        ]
        / summary[
            "Products"
        ],
        0,
    )

    return summary


# ============================================================
# KPI Section
# ============================================================

def _render_kpis(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Merchandise KPI Pulse",
        (
            "Commercial performance of products "
            "inside the active filters and RLS scope."
        ),
    )

    revenue = _safe_float(
        products[
            "Revenue"
        ].sum()
    )

    profit = _safe_float(
        products[
            "GrossProfit"
        ].sum()
    )

    gross_units = _safe_float(
        products[
            "GrossUnits"
        ].sum()
    )

    returned_units = (
        _safe_float(
            products[
                "ReturnedUnits"
            ].sum()
        )
    )

    net_units = _safe_float(
        products[
            "NetUnits"
        ].sum()
    )

    margin = (
        profit
        / revenue
        * 100
        if revenue
        else 0
    )

    return_rate = (
        returned_units
        / gross_units
        * 100
        if gross_units
        else 0
    )

    discount_value = (
        _safe_float(
            products[
                "DiscountAmount"
            ].sum()
        )
    )

    row = st.columns(4)

    metric(
        row[0],
        "Product Revenue",
        money(revenue),
    )

    metric(
        row[1],
        "Gross Profit",
        money(profit),
    )

    metric(
        row[2],
        "Portfolio Margin",
        percentage(margin),
    )

    metric(
        row[3],
        "Products Sold",
        number(
            products[
                "ProductId"
            ].nunique()
        ),
    )

    row = st.columns(4)

    metric(
        row[0],
        "Net Units",
        number(net_units),
    )

    metric(
        row[1],
        "Return Rate",
        percentage(
            return_rate
        ),
    )

    metric(
        row[2],
        "Discount Amount",
        money(
            discount_value
        ),
    )

    metric(
        row[3],
        "Class A Products",
        number(
            products[
                "ABCClass"
            ]
            .eq("A")
            .sum()
        ),
    )


# ============================================================
# Signals
# ============================================================

def _render_signals(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Merchandising Signals",
        (
            "Quick portfolio indicators for "
            "commercial decision-making."
        ),
    )

    top_revenue = (
        products.iloc[0]
    )

    top_profit = (
        products.nlargest(
            1,
            "GrossProfit",
        )
        .iloc[0]
    )

    highest_return = (
        products.nlargest(
            1,
            "ReturnRatePct",
        )
        .iloc[0]
    )

    highest_discount = (
        products.nlargest(
            1,
            "DiscountDependencyPct",
        )
        .iloc[0]
    )

    columns = st.columns(4)

    with columns[0]:
        insight_card(
            "TOP REVENUE SKU",
            str(
                top_revenue["SKU"]
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
            "TOP PROFIT SKU",
            str(
                top_profit["SKU"]
            ),
            money(
                top_profit[
                    "GrossProfit"
                ]
            ),
            "green",
        )

    with columns[2]:
        insight_card(
            "RETURN RISK SKU",
            str(
                highest_return[
                    "SKU"
                ]
            ),
            percentage(
                highest_return[
                    "ReturnRatePct"
                ]
            ),
            "red",
        )

    with columns[3]:
        insight_card(
            "DISCOUNT DEPENDENCY",
            str(
                highest_discount[
                    "SKU"
                ]
            ),
            percentage(
                highest_discount[
                    "DiscountDependencyPct"
                ]
            ),
            "gold",
        )


# ============================================================
# Category
# ============================================================

def _render_category_analysis(
    categories: pd.DataFrame,
) -> None:
    section_header(
        "Category Economics",
        (
            "Revenue, profitability, returns "
            "and product productivity by category."
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
                "Products",
                "GrossProfit",
                "ReturnRatePct",
                "DiscountRatePct",
                "RevenuePerProduct",
            ],
            title=(
                "Category Revenue & Margin"
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
            size="NetUnits",
            color="ReturnRatePct",
            hover_name=(
                "CategoryName"
            ),
            hover_data=[
                "Products",
                "RevenuePerProduct",
                "DiscountRatePct",
            ],
            title=(
                "Category Value / "
                "Margin / Return Matrix"
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

    figure = px.scatter(
        categories,
        x="RevenuePerProduct",
        y="ReturnRatePct",
        size="Revenue",
        color="GrossMarginPct",
        hover_name="CategoryName",
        title=(
            "Category Product Productivity"
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
# ABC / Pareto
# ============================================================

def _render_pareto(
    products: pd.DataFrame,
) -> None:
    section_header(
        "ABC / Pareto Revenue Analysis",
        (
            "Revenue concentration identifying "
            "the products responsible for the "
            "majority of portfolio value."
        ),
    )

    count = min(
        75,
        len(products),
    )

    pareto = (
        products.head(
            count
        )
        .copy()
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=pareto["SKU"],
            y=pareto["Revenue"],
            name="Revenue",
            marker_color=(
                COLORS[
                    "uae_green"
                ]
            ),
            customdata=(
                pareto[
                    [
                        "ProductName",
                        "ABCClass",
                        "GrossMarginPct",
                    ]
                ]
            ),
            hovertemplate=(
                "SKU: %{x}<br>"
                "Product: "
                "%{customdata[0]}<br>"
                "Revenue: "
                "%{y:,.0f}<br>"
                "ABC: "
                "%{customdata[1]}<br>"
                "Margin: "
                "%{customdata[2]:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=pareto["SKU"],
            y=pareto[
                "CumulativeRevenuePct"
            ],
            name="Cumulative Revenue %",
            yaxis="y2",
            mode="lines",
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
            "Product Revenue Pareto Curve"
        ),

        xaxis_title=None,

        yaxis_title="Revenue",

        yaxis2=dict(
            title=(
                "Cumulative Revenue %"
            ),
            overlaying="y",
            side="right",
            range=[
                0,
                105,
            ],
            gridcolor=(
                "rgba(0,0,0,0)"
            ),
        ),
    )

    st.plotly_chart(
        style_figure(
            figure,
            520,
        ),
        use_container_width=True,
    )

    abc = (
        products.groupby(
            "ABCClass",
            as_index=False,
        )
        .agg(
            Products=(
                "ProductId",
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
            NetUnits=(
                "NetUnits",
                "sum",
            ),
        )
    )

    total = _safe_float(
        abc[
            "Revenue"
        ].sum()
    )

    abc[
        "RevenueSharePct"
    ] = (
        abc["Revenue"]
        / total
        * 100
        if total
        else 0
    )

    left, right = (
        st.columns(2)
    )

    with left:
        figure = px.bar(
            abc,
            x="ABCClass",
            y="Revenue",
            color="ABCClass",
            text="RevenueSharePct",
            title=(
                "Revenue by ABC Class"
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

    with right:
        figure = px.bar(
            abc,
            x="ABCClass",
            y="Products",
            color="ABCClass",
            title=(
                "Product Count by ABC Class"
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

        st.plotly_chart(
            style_figure(
                figure,
                400,
                legend=False,
            ),
            use_container_width=True,
        )


# ============================================================
# Product Portfolio Matrix
# ============================================================

def _render_portfolio_matrix(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Product Portfolio Matrix",
        (
            "Revenue scale, margin quality, "
            "volume and strategic product segment."
        ),
    )

    revenue_median = (
        products[
            "Revenue"
        ].median()
    )

    margin_median = (
        products[
            "GrossMarginPct"
        ].median()
    )

    figure = px.scatter(
        products,
        x="Revenue",
        y="GrossMarginPct",
        size="NetUnits",
        color="PortfolioQuadrant",
        hover_name="ProductName",
        hover_data=[
            "SKU",
            "CategoryName",
            "SubcategoryName",
            "BrandName",
            "ReturnRatePct",
            "DiscountDependencyPct",
            "ProductScore",
        ],
        title=(
            "Revenue / Margin "
            "Product Quadrants"
        ),
        color_discrete_map={
            "Revenue & Margin Leaders":
                COLORS[
                    "uae_green"
                ],

            "High Revenue / Margin Pressure":
                COLORS["gold"],

            "Niche Margin Performers":
                COLORS["info"],

            "Portfolio Review":
                COLORS[
                    "uae_red"
                ],
        },
        opacity=.72,
    )

    figure.add_vline(
        x=revenue_median,
        line_dash="dash",
        opacity=.5,
    )

    figure.add_hline(
        y=margin_median,
        line_dash="dash",
        opacity=.5,
    )

    st.plotly_chart(
        style_figure(
            figure,
            540,
        ),
        use_container_width=True,
    )


# ============================================================
# Profitability
# ============================================================

def _render_profitability(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Product Profitability",
        (
            "Gross profit generation, unit economics "
            "and commercial efficiency."
        ),
    )

    count = min(
        20,
        len(products),
    )

    left, right = st.columns(2)

    with left:
        top_profit = (
            products.nlargest(
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
            y="SKU",
            orientation="h",
            color="GrossMarginPct",
            hover_name="ProductName",
            hover_data=[
                "Revenue",
                "NetUnits",
            ],
            title=(
                "Top Products by Gross Profit"
            ),
            color_continuous_scale=(
                "YlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                560,
            ),
            use_container_width=True,
        )

    with right:
        top_unit_profit = (
            products.nlargest(
                count,
                "ProfitPerUnit",
            )
            .sort_values(
                "ProfitPerUnit"
            )
        )

        figure = px.bar(
            top_unit_profit,
            x="ProfitPerUnit",
            y="SKU",
            orientation="h",
            color="Revenue",
            hover_name="ProductName",
            hover_data=[
                "GrossMarginPct",
                "NetUnits",
            ],
            title=(
                "Highest Profit per Net Unit"
            ),
            color_continuous_scale=(
                "Viridis"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                560,
            ),
            use_container_width=True,
        )

    figure = px.scatter(
        products,
        x="RevenuePerUnit",
        y="ProfitPerUnit",
        size="NetUnits",
        color="GrossMarginPct",
        hover_name="ProductName",
        hover_data=[
            "SKU",
            "CategoryName",
            "ReturnRatePct",
        ],
        title=(
            "Unit Economics Matrix"
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


# ============================================================
# Discount Dependency
# ============================================================

def _render_discount_analysis(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Discount Dependency",
        (
            "Identify products where commercial "
            "performance is highly associated with "
            "discounted sales."
        ),
    )

    count = min(
        25,
        len(products),
    )

    left, right = (
        st.columns(2)
    )

    with left:
        high_discount = (
            products.nlargest(
                count,
                "DiscountDependencyPct",
            )
            .sort_values(
                "DiscountDependencyPct"
            )
        )

        figure = px.bar(
            high_discount,
            x="DiscountDependencyPct",
            y="SKU",
            orientation="h",
            color="GrossMarginPct",
            hover_name="ProductName",
            hover_data=[
                "Revenue",
                "CategoryName",
            ],
            title=(
                "Highest Discount Dependency"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                590,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            products,
            x="DiscountDependencyPct",
            y="GrossMarginPct",
            size="Revenue",
            color="ReturnRatePct",
            hover_name="ProductName",
            hover_data=[
                "SKU",
                "CategoryName",
                "BrandName",
            ],
            title=(
                "Discount / Margin / Return Matrix"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
            opacity=.7,
        )

        st.plotly_chart(
            style_figure(
                figure,
                590,
            ),
            use_container_width=True,
        )


# ============================================================
# Return Risk
# ============================================================

def _render_return_analysis(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Product Return Risk",
        (
            "Products with elevated return exposure "
            "and potential margin pressure."
        ),
    )

    count = min(
        25,
        len(products),
    )

    risk = (
        products.nlargest(
            count,
            "ReturnRatePct",
        )
        .sort_values(
            "ReturnRatePct"
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            risk,
            x="ReturnRatePct",
            y="SKU",
            orientation="h",
            color="Revenue",
            hover_name="ProductName",
            hover_data=[
                "CategoryName",
                "GrossMarginPct",
                "ReturnedUnits",
            ],
            title=(
                "Highest Product Return Rates"
            ),
            color_continuous_scale=(
                "Reds"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                590,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            products,
            x="ReturnRatePct",
            y="GrossMarginPct",
            size="Revenue",
            color="BusinessFlag",
            hover_name="ProductName",
            hover_data=[
                "SKU",
                "CategoryName",
                "DiscountDependencyPct",
            ],
            title=(
                "Return Rate vs Margin"
            ),
            color_discrete_map={
                "Normal":
                    COLORS[
                        "muted"
                    ],

                "High Return / Low Margin":
                    COLORS[
                        "uae_red"
                    ],

                "Discount Dependency / Margin Risk":
                    "#E88A32",

                "High Revenue / Margin Pressure":
                    COLORS["gold"],

                "High Value Product":
                    COLORS[
                        "uae_green"
                    ],
            },
            opacity=.72,
        )

        st.plotly_chart(
            style_figure(
                figure,
                590,
            ),
            use_container_width=True,
        )


# ============================================================
# Brand Analysis
# ============================================================

def _render_brand_analysis(
    brands: pd.DataFrame,
) -> None:
    section_header(
        "Brand Performance",
        (
            "Revenue, profitability and "
            "product productivity by brand."
        ),
    )

    count = min(
        20,
        len(brands),
    )

    top = (
        brands.nlargest(
            count,
            "Revenue",
        )
        .sort_values(
            "Revenue"
        )
    )

    left, right = st.columns(2)

    with left:
        figure = px.bar(
            top,
            x="Revenue",
            y="BrandName",
            orientation="h",
            color="GrossMarginPct",
            hover_data=[
                "Products",
                "GrossProfit",
                "ReturnRatePct",
                "RevenuePerProduct",
            ],
            title=(
                "Top Brands by Revenue"
            ),
            color_continuous_scale=(
                "RdYlGn"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                560,
            ),
            use_container_width=True,
        )

    with right:
        figure = px.scatter(
            brands,
            x="Revenue",
            y="GrossMarginPct",
            size="Products",
            color="ReturnRatePct",
            hover_name="BrandName",
            hover_data=[
                "GrossProfit",
                "RevenuePerProduct",
                "DiscountRatePct",
            ],
            title=(
                "Brand Value / "
                "Margin / Return Matrix"
            ),
            color_continuous_scale=(
                "YlOrRd"
            ),
        )

        st.plotly_chart(
            style_figure(
                figure,
                560,
            ),
            use_container_width=True,
        )


# ============================================================
# Subcategory Analysis
# ============================================================

def _render_subcategory_analysis(
    subcategories: pd.DataFrame,
) -> None:
    section_header(
        "Subcategory Performance",
        (
            "Mid-level portfolio diagnostics "
            "between category and SKU."
        ),
    )

    count = min(
        25,
        len(subcategories),
    )

    top = (
        subcategories.nlargest(
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
        y="SubcategoryName",
        orientation="h",
        color="GrossMarginPct",
        hover_data=[
            "Products",
            "ReturnRatePct",
            "RevenuePerProduct",
        ],
        title=(
            "Top Subcategories by Revenue"
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
# Product Score
# ============================================================

def _render_product_score(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Composite Product Performance Score",
        (
            "Relative prioritization score combining "
            "revenue, profit, margin, velocity, "
            "return health and discount health."
        ),
    )

    top = (
        products.nlargest(
            min(
                40,
                len(products),
            ),
            "ProductScore",
        )
        .sort_values(
            "ProductScore"
        )
    )

    figure = px.bar(
        top,
        x="ProductScore",
        y="SKU",
        orientation="h",
        color="PerformanceTier",
        hover_name="ProductName",
        hover_data=[
            "Revenue",
            "GrossProfit",
            "GrossMarginPct",
            "ReturnRatePct",
            "DiscountDependencyPct",
        ],
        title=(
            "Top Composite Product Scores"
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
            720,
        ),
        use_container_width=True,
    )

    st.caption(
        "Relative score weights: Revenue 25%, "
        "Gross Profit 25%, Margin 15%, "
        "Net Unit Velocity 15%, Return Health 10%, "
        "Discount Health 10%. It is a portfolio "
        "prioritization aid, not an accounting KPI."
    )


# ============================================================
# Outlier Screening
# ============================================================

def _render_outliers(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Product Outlier Screening",
        (
            "Statistical screening for unusual "
            "revenue, margin, return or discount behavior."
        ),
    )

    products = products.copy()

    products[
        "OutlierFlag"
    ] = (
        (
            products[
                "RevenueZScore"
            ].abs()
            >= 2
        )
        | (
            products[
                "MarginZScore"
            ].abs()
            >= 2
        )
        | (
            products[
                "ReturnZScore"
            ]
            >= 2
        )
        | (
            products[
                "DiscountZScore"
            ]
            >= 2
        )
    )

    candidates = (
        products[
            products[
                "OutlierFlag"
            ]
        ]
        .copy()
    )

    row = st.columns(4)

    metric(
        row[0],
        "Revenue Outliers",
        number(
            (
                products[
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
                products[
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
                products[
                    "ReturnZScore"
                ]
                >= 2
            ).sum()
        ),
    )

    metric(
        row[3],
        "Discount Outliers",
        number(
            (
                products[
                    "DiscountZScore"
                ]
                >= 2
            ).sum()
        ),
    )

    if candidates.empty:
        st.success(
            "No products exceed the current "
            "outlier screening thresholds."
        )
        return

    st.dataframe(
        candidates[
            [
                "SKU",
                "ProductName",
                "CategoryName",
                "Revenue",
                "GrossMarginPct",
                "ReturnRatePct",
                "DiscountDependencyPct",
                "RevenueZScore",
                "MarginZScore",
                "ReturnZScore",
                "DiscountZScore",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config=(
            dataframe_config()
        ),
    )


# ============================================================
# Business Flags
# ============================================================

def _render_business_flags(
    products: pd.DataFrame,
) -> None:
    section_header(
        "Merchandising Action Queue",
        (
            "Rule-based product flags combining "
            "revenue, margin, returns and discounts."
        ),
    )

    flags = (
        products.groupby(
            "BusinessFlag",
            as_index=False,
        )
        .agg(
            Products=(
                "ProductId",
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
        y="Products",
        color="BusinessFlag",
        text="Products",
        hover_data=[
            "Revenue",
            "GrossProfit",
        ],
        title=(
            "Product Business Flags"
        ),
        color_discrete_map={
            "Normal":
                COLORS["muted"],

            "High Return / Low Margin":
                COLORS[
                    "uae_red"
                ],

            "Discount Dependency / Margin Risk":
                "#E88A32",

            "High Revenue / Margin Pressure":
                COLORS["gold"],

            "High Value Product":
                COLORS[
                    "uae_green"
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
            420,
            legend=False,
        ),
        use_container_width=True,
    )

    review = (
        products[
            products[
                "BusinessFlag"
            ]
            != "Normal"
        ]
        .sort_values(
            "Revenue",
            ascending=False,
        )
        .copy()
    )

    if not review.empty:
        st.dataframe(
            review[
                [
                    "SKU",
                    "ProductName",
                    "CategoryName",
                    "BrandName",
                    "Revenue",
                    "GrossProfit",
                    "GrossMarginPct",
                    "ReturnRatePct",
                    "DiscountDependencyPct",
                    "ProductScore",
                    "BusinessFlag",
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
    products: pd.DataFrame,
    categories: pd.DataFrame,
    brands: pd.DataFrame,
    subcategories: pd.DataFrame,
) -> None:
    section_header(
        "Merchandise Data Explorer",
        (
            "Filtered product, category, brand "
            "and subcategory datasets."
        ),
    )

    (
        product_tab,
        category_tab,
        brand_tab,
        subcategory_tab,
    ) = st.tabs(
        [
            "Products",
            "Categories",
            "Brands",
            "Subcategories",
        ]
    )

    with product_tab:
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
                "Export filtered product data"
            ),
            file_name=(
                "products_filtered.csv"
            ),
            key=(
                "products_export_detail"
            ),
        )

    with category_tab:
        st.dataframe(
            categories,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=categories,
            label=(
                "Export category analysis"
            ),
            file_name=(
                "product_categories_filtered.csv"
            ),
            key=(
                "products_export_categories"
            ),
        )

    with brand_tab:
        st.dataframe(
            brands,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=brands,
            label=(
                "Export brand analysis"
            ),
            file_name=(
                "product_brands_filtered.csv"
            ),
            key=(
                "products_export_brands"
            ),
        )

    with subcategory_tab:
        st.dataframe(
            subcategories,
            use_container_width=True,
            hide_index=True,
            column_config=(
                dataframe_config()
            ),
        )

        secure_csv_download(
            user=user,
            dataframe=subcategories,
            label=(
                "Export subcategory analysis"
            ),
            file_name=(
                "product_subcategories_filtered.csv"
            ),
            key=(
                "products_export_subcategories"
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
        "Merchandise & Product Command Center",
        (
            "Advanced product intelligence covering "
            "revenue, profitability, ABC/Pareto, category, "
            "brand, subcategory, discount dependency, "
            "returns, unit economics and portfolio risk."
        ),
        "UAE MERCHANDISING INTELLIGENCE",
    )

    st.caption(
        "Reporting period: "
        f"{_period_label(filters)}"
    )

    raw_products = (
        get_filtered_product_performance(
            user,
            filters,
        )
    )

    if raw_products.empty:
        st.warning(
            "No product performance data "
            "matches the active filters."
        )
        return

    products = _prepare_products(
        raw_products
    )

    categories = (
        _aggregate_dimension(
            products,
            [
                "CategoryId",
                "CategoryName",
            ],
        )
    )

    brands = (
        _aggregate_dimension(
            products,
            [
                "BrandId",
                "BrandName",
            ],
        )
    )

    subcategories = (
        _aggregate_dimension(
            products,
            [
                "SubcategoryId",
                "SubcategoryName",
                "CategoryName",
            ],
        )
    )

    _render_kpis(
        products
    )

    _render_signals(
        products
    )

    _render_category_analysis(
        categories
    )

    _render_pareto(
        products
    )

    _render_portfolio_matrix(
        products
    )

    _render_profitability(
        products
    )

    _render_discount_analysis(
        products
    )

    _render_return_analysis(
        products
    )

    _render_brand_analysis(
        brands
    )

    _render_subcategory_analysis(
        subcategories
    )

    _render_product_score(
        products
    )

    _render_outliers(
        products
    )

    _render_business_flags(
        products
    )

    _render_data_explorer(
        user,
        products,
        categories,
        brands,
        subcategories,
    )