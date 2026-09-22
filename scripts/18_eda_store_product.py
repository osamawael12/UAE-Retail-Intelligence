"""
UAE Retail Intelligence Platform
EDA 03 - Store & Product Analysis

Analysis:
- Store revenue, profit and margin
- Emirate performance
- Store performance quadrants
- Store return-rate exploration
- Category and brand performance
- Product revenue concentration
- Pareto curve
- Discount dependency
- Product profitability vs return rate
- Product business-risk candidates

Outputs:
assets/eda/03_store_product/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.data_access import (
    get_product_performance,
    get_sales_detail,
    get_store_performance,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/03_store_product"
)


def build_emirate_summary(
    stores: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        stores.groupby(
            "EmirateName",
            as_index=False,
        )
        .agg(
            Stores=(
                "StoreId",
                "nunique",
            ),
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
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
        )
    )

    summary[
        "GrossMarginPct"
    ] = (
        summary[
            "GrossProfit"
        ]
        / summary[
            "Revenue"
        ]
        .replace(
            0,
            np.nan,
        )
        * 100
    )

    summary[
        "ReturnRatePct"
    ] = (
        summary[
            "ReturnedUnits"
        ]
        / summary[
            "GrossUnits"
        ]
        .replace(
            0,
            np.nan,
        )
        * 100
    )

    summary[
        "RevenuePerStore"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "Stores"
        ]
    )

    summary[
        "RevenueContributionPct"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "Revenue"
        ].sum()
        * 100
    )

    return (
        summary.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def build_category_summary(
    sales_detail: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales_detail.groupby(
            "CategoryName",
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
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
            DiscountAmount=(
                "DiscountAmount",
                "sum",
            ),
            GrossSales=(
                "GrossSales",
                "sum",
            ),
        )
    )

    summary[
        "GrossMarginPct"
    ] = (
        summary[
            "GrossProfit"
        ]
        / summary[
            "Revenue"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    summary[
        "ReturnRatePct"
    ] = (
        summary[
            "ReturnedUnits"
        ]
        / summary[
            "GrossUnits"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    summary[
        "DiscountRatePct"
    ] = (
        summary[
            "DiscountAmount"
        ]
        / summary[
            "GrossSales"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    return (
        summary.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def build_brand_summary(
    sales_detail: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales_detail.groupby(
            "BrandName",
            as_index=False,
        )
        .agg(
            Products=(
                "ProductId",
                "nunique",
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
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
        )
    )

    summary[
        "GrossMarginPct"
    ] = (
        summary[
            "GrossProfit"
        ]
        / summary[
            "Revenue"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    summary[
        "ReturnRatePct"
    ] = (
        summary[
            "ReturnedUnits"
        ]
        / summary[
            "GrossUnits"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    return (
        summary.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def build_pareto(
    products: pd.DataFrame,
) -> pd.DataFrame:
    pareto = (
        products[
            [
                "ProductId",
                "SKU",
                "ProductName",
                "CategoryName",
                "Revenue",
            ]
        ]
        .sort_values(
            [
                "Revenue",
                "ProductId",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    pareto[
        "ProductRank"
    ] = (
        np.arange(
            1,
            len(pareto) + 1,
        )
    )

    total_revenue = (
        pareto[
            "Revenue"
        ].sum()
    )

    pareto[
        "RevenueContributionPct"
    ] = (
        pareto[
            "Revenue"
        ]
        / total_revenue
        * 100
    )

    pareto[
        "CumulativeRevenue"
    ] = (
        pareto[
            "Revenue"
        ].cumsum()
    )

    pareto[
        "CumulativeRevenuePct"
    ] = (
        pareto[
            "CumulativeRevenue"
        ]
        / total_revenue
        * 100
    )

    pareto[
        "CumulativeProductPct"
    ] = (
        pareto[
            "ProductRank"
        ]
        / len(pareto)
        * 100
    )

    pareto[
        "ABCClass"
    ] = np.select(
        [
            pareto[
                "CumulativeRevenuePct"
            ]
            <= 80,

            pareto[
                "CumulativeRevenuePct"
            ]
            <= 95,
        ],
        [
            "A",
            "B",
        ],
        default="C",
    )

    return pareto


def main() -> None:
    configure_visuals()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print(
        "EDA 03 - STORE & PRODUCT ANALYSIS"
    )
    print("=" * 78)

    stores = (
        get_store_performance()
    )

    products = (
        get_product_performance()
    )

    sales_detail = (
        get_sales_detail()
    )

    # ========================================================
    # Store / Emirate summaries
    # ========================================================

    emirates = (
        build_emirate_summary(
            stores
        )
    )

    save_csv(
        emirates,
        OUTPUT_DIR
        / "emirate_summary.csv",
    )

    store_output = (
        stores.sort_values(
            "Revenue",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    store_output[
        "RevenueRank"
    ] = (
        np.arange(
            1,
            len(
                store_output
            )
            + 1,
        )
    )

    save_csv(
        store_output,
        OUTPUT_DIR
        / "store_performance.csv",
    )

    print(
        "\nEmirate Performance:"
    )

    print(
        emirates[
            [
                "EmirateName",
                "Stores",
                "Revenue",
                "RevenuePerStore",
                "GrossMarginPct",
                "ReturnRatePct",
            ]
        ]
        .round(
            2
        )
        .to_string(
            index=False
        )
    )

    # ========================================================
    # Emirate Revenue
    # ========================================================

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    axis = sns.barplot(
        data=emirates,
        y="EmirateName",
        x="Revenue",
        color="#2563EB",
    )

    plt.title(
        "Revenue by Emirate"
    )

    plt.xlabel(
        "Revenue"
    )

    plt.ylabel(
        ""
    )

    format_aed_axis(
        axis,
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "revenue_by_emirate.png"
    )

    # ========================================================
    # Revenue per Store by Emirate
    # ========================================================

    revenue_per_store = (
        emirates.sort_values(
            "RevenuePerStore",
            ascending=False,
        )
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    axis = sns.barplot(
        data=revenue_per_store,
        y="EmirateName",
        x="RevenuePerStore",
        color="#0F766E",
    )

    plt.title(
        "Average Revenue per Store by Emirate"
    )

    plt.xlabel(
        "Revenue per Store"
    )

    plt.ylabel(
        ""
    )

    format_aed_axis(
        axis,
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "revenue_per_store_by_emirate.png"
    )

    # ========================================================
    # Store Revenue vs Margin
    # ========================================================

    median_revenue = float(
        stores[
            "Revenue"
        ].median()
    )

    median_margin = float(
        stores[
            "GrossMarginPct"
        ].median()
    )

    stores_quadrant = (
        stores.copy()
    )

    stores_quadrant[
        "PerformanceQuadrant"
    ] = np.select(
        [
            (
                stores_quadrant[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                stores_quadrant[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),

            (
                stores_quadrant[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                stores_quadrant[
                    "GrossMarginPct"
                ]
                < median_margin
            ),

            (
                stores_quadrant[
                    "Revenue"
                ]
                < median_revenue
            )
            & (
                stores_quadrant[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),
        ],
        [
            "High Revenue / High Margin",
            "High Revenue / Low Margin",
            "Low Revenue / High Margin",
        ],
        default=(
            "Low Revenue / Low Margin"
        ),
    )

    save_csv(
        stores_quadrant,
        OUTPUT_DIR
        / "store_performance_quadrants.csv",
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    axis = sns.scatterplot(
        data=stores_quadrant,
        x="Revenue",
        y="GrossMarginPct",
        hue="PerformanceQuadrant",
        size="Orders",
        sizes=(
            80,
            350,
        ),
        alpha=0.8,
    )

    plt.axvline(
        median_revenue,
        color="#64748B",
        linestyle="--",
        linewidth=1,
    )

    plt.axhline(
        median_margin,
        color="#64748B",
        linestyle="--",
        linewidth=1,
    )

    for row in (
        stores_quadrant.itertuples(
            index=False
        )
    ):
        plt.annotate(
            row.StoreCode,
            (
                row.Revenue,
                row.GrossMarginPct,
            ),
            xytext=(
                4,
                4,
            ),
            textcoords="offset points",
            fontsize=8,
        )

    plt.title(
        "Store Revenue vs Gross Margin"
    )

    plt.xlabel(
        "Revenue"
    )

    plt.ylabel(
        "Gross Margin (%)"
    )

    format_aed_axis(
        axis,
        "x",
    )

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "store_revenue_margin_quadrant.png"
    )

    # ========================================================
    # Store Return Rate
    # ========================================================

    stores_return = (
        stores.sort_values(
            "ReturnRatePct",
            ascending=False,
        )
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sns.barplot(
        data=stores_return,
        y="StoreCode",
        x="ReturnRatePct",
        hue="EmirateName",
        dodge=False,
    )

    plt.title(
        "Store Return Rate"
    )

    plt.xlabel(
        "Return Rate (%)"
    )

    plt.ylabel(
        "Store"
    )

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "store_return_rate.png"
    )

    # ========================================================
    # Category summary
    # ========================================================

    categories = (
        build_category_summary(
            sales_detail
        )
    )

    save_csv(
        categories,
        OUTPUT_DIR
        / "category_summary.csv",
    )

    print(
        "\nCategory Performance:"
    )

    print(
        categories[
            [
                "CategoryName",
                "Revenue",
                "GrossProfit",
                "GrossMarginPct",
                "ReturnRatePct",
                "DiscountRatePct",
            ]
        ]
        .round(
            2
        )
        .to_string(
            index=False
        )
    )

    # ========================================================
    # Category Revenue / Profit
    # ========================================================

    category_long = (
        categories[
            [
                "CategoryName",
                "Revenue",
                "GrossProfit",
            ]
        ]
        .melt(
            id_vars=(
                "CategoryName"
            ),
            var_name="Metric",
            value_name="Value",
        )
    )

    plt.figure(
        figsize=(
            14,
            7,
        )
    )

    axis = sns.barplot(
        data=category_long,
        x="CategoryName",
        y="Value",
        hue="Metric",
    )

    plt.title(
        "Category Revenue and Gross Profit"
    )

    plt.xlabel(
        ""
    )

    plt.ylabel(
        "AED"
    )

    plt.xticks(
        rotation=30
    )

    format_aed_axis(
        axis,
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "category_revenue_profit.png"
    )

    # ========================================================
    # Category Margin vs Return Rate
    # ========================================================

    plt.figure(
        figsize=(
            11,
            7,
        )
    )

    sns.scatterplot(
        data=categories,
        x="ReturnRatePct",
        y="GrossMarginPct",
        size="Revenue",
        hue="CategoryName",
        sizes=(
            150,
            700,
        ),
        alpha=0.85,
    )

    for row in (
        categories.itertuples(
            index=False
        )
    ):
        plt.annotate(
            row.CategoryName,
            (
                row.ReturnRatePct,
                row.GrossMarginPct,
            ),
            xytext=(
                5,
                5,
            ),
            textcoords=(
                "offset points"
            ),
            fontsize=9,
        )

    plt.title(
        "Category Margin vs Return Rate"
    )

    plt.xlabel(
        "Return Rate (%)"
    )

    plt.ylabel(
        "Gross Margin (%)"
    )

    plt.legend().remove()

    save_figure(
        OUTPUT_DIR
        / "category_margin_return_rate.png"
    )

    # ========================================================
    # Brand performance
    # ========================================================

    brands = (
        build_brand_summary(
            sales_detail
        )
    )

    save_csv(
        brands,
        OUTPUT_DIR
        / "brand_summary.csv",
    )

    top_brands = (
        brands.head(15)
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    axis = sns.barplot(
        data=top_brands,
        y="BrandName",
        x="Revenue",
        color="#7C3AED",
    )

    plt.title(
        "Top 15 Brands by Revenue"
    )

    plt.xlabel(
        "Revenue"
    )

    plt.ylabel(
        ""
    )

    format_aed_axis(
        axis,
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "top_brands_revenue.png"
    )

    # ========================================================
    # Pareto
    # ========================================================

    pareto = (
        build_pareto(
            products
        )
    )

    save_csv(
        pareto,
        OUTPUT_DIR
        / "product_pareto.csv",
    )

    eighty_boundary = (
        pareto.loc[
            pareto[
                "CumulativeRevenuePct"
            ]
            >= 80
        ]
        .iloc[0]
    )

    products_for_80 = int(
        eighty_boundary[
            "ProductRank"
        ]
    )

    product_pct_for_80 = float(
        eighty_boundary[
            "CumulativeProductPct"
        ]
    )

    plt.figure(
        figsize=(
            13,
            7,
        )
    )

    plt.plot(
        pareto[
            "CumulativeProductPct"
        ],
        pareto[
            "CumulativeRevenuePct"
        ],
        color="#2563EB",
        linewidth=2.5,
    )

    plt.axhline(
        80,
        color="#DC2626",
        linestyle="--",
        label="80% Revenue",
    )

    plt.axvline(
        product_pct_for_80,
        color="#0F766E",
        linestyle="--",
        label=(
            f"{product_pct_for_80:.1f}% "
            "of Products"
        ),
    )

    plt.title(
        "Product Pareto Curve"
    )

    plt.xlabel(
        "Cumulative Products (%)"
    )

    plt.ylabel(
        "Cumulative Revenue (%)"
    )

    plt.xlim(
        0,
        100,
    )

    plt.ylim(
        0,
        102,
    )

    plt.legend()

    save_figure(
        OUTPUT_DIR
        / "product_pareto_curve.png"
    )

    abc_summary = (
        pareto.groupby(
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
        )
    )

    abc_summary[
        "ProductPct"
    ] = (
        abc_summary[
            "Products"
        ]
        / abc_summary[
            "Products"
        ].sum()
        * 100
    )

    abc_summary[
        "RevenuePct"
    ] = (
        abc_summary[
            "Revenue"
        ]
        / abc_summary[
            "Revenue"
        ].sum()
        * 100
    )

    save_csv(
        abc_summary,
        OUTPUT_DIR
        / "abc_summary.csv",
    )

    # ========================================================
    # Product profitability vs returns
    # ========================================================

    product_analysis = (
        products.copy()
    )

    median_product_revenue = float(
        product_analysis[
            "Revenue"
        ].median()
    )

    median_product_margin = float(
        product_analysis[
            "GrossMarginPct"
        ].median()
    )

    return_q75 = float(
        product_analysis[
            "ReturnRatePct"
        ].quantile(
            0.75
        )
    )

    product_analysis[
        "BusinessFlag"
    ] = np.select(
        [
            (
                product_analysis[
                    "Revenue"
                ]
                >= median_product_revenue
            )
            & (
                product_analysis[
                    "ReturnRatePct"
                ]
                >= return_q75
            ),

            (
                product_analysis[
                    "Revenue"
                ]
                >= median_product_revenue
            )
            & (
                product_analysis[
                    "GrossMarginPct"
                ]
                < median_product_margin
            ),

            (
                product_analysis[
                    "DiscountDependencyPct"
                ]
                >= 50
            ),
        ],
        [
            "High Revenue / High Returns",
            "High Revenue / Low Margin",
            "High Discount Dependency",
        ],
        default="Normal",
    )

    risk_products = (
        product_analysis.loc[
            product_analysis[
                "BusinessFlag"
            ]
            != "Normal"
        ]
        .sort_values(
            "Revenue",
            ascending=False,
        )
    )

    save_csv(
        risk_products,
        OUTPUT_DIR
        / "product_business_flags.csv",
    )

    # ========================================================
    # Product Revenue vs Return Rate
    # ========================================================

    plot_products = (
        product_analysis.loc[
            product_analysis[
                "GrossUnits"
            ]
            >= 50
        ]
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sns.scatterplot(
        data=plot_products,
        x="ReturnRatePct",
        y="Revenue",
        hue="CategoryName",
        size="GrossProfit",
        sizes=(
            20,
            250,
        ),
        alpha=0.65,
    )

    plt.title(
        "Product Revenue vs Return Rate"
    )

    plt.xlabel(
        "Return Rate (%)"
    )

    plt.ylabel(
        "Revenue"
    )

    format_aed_axis(
        plt.gca(),
        "y",
    )

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "product_revenue_return_rate.png"
    )

    # ========================================================
    # Discount Dependency
    # ========================================================

    high_discount = (
        products.loc[
            products[
                "GrossUnits"
            ]
            >= 50
        ]
        .sort_values(
            "DiscountDependencyPct",
            ascending=False,
        )
        .head(25)
    )

    save_csv(
        high_discount,
        OUTPUT_DIR
        / "high_discount_dependency_products.csv",
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sns.barplot(
        data=high_discount,
        y="SKU",
        x="DiscountDependencyPct",
        hue="CategoryName",
        dodge=False,
    )

    plt.title(
        "Top Products by Discount Dependency"
    )

    plt.xlabel(
        "Discount Dependency (%)"
    )

    plt.ylabel(
        "Product"
    )

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "discount_dependency.png"
    )

    # ========================================================
    # Business observations
    # ========================================================

    observations = []

    top_emirate = (
        emirates.iloc[0]
    )

    observations.append(
        {
            "Area": "Emirates",
            "Observation": (
                f"{top_emirate['EmirateName']} "
                "generated the highest total revenue "
                f"at AED {float(top_emirate['Revenue']):,.2f}."
            ),
        }
    )

    best_revenue_per_store = (
        emirates.sort_values(
            "RevenuePerStore",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area": "Emirates",
            "Observation": (
                f"{best_revenue_per_store['EmirateName']} "
                "had the highest average revenue per store "
                f"at AED "
                f"{float(best_revenue_per_store['RevenuePerStore']):,.2f}."
            ),
        }
    )

    highest_return_category = (
        categories.sort_values(
            "ReturnRatePct",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area": "Products",
            "Observation": (
                f"{highest_return_category['CategoryName']} "
                "had the highest category return rate at "
                f"{float(highest_return_category['ReturnRatePct']):.2f}%."
            ),
        }
    )

    observations.append(
        {
            "Area": "Pareto",
            "Observation": (
                f"{products_for_80} products "
                f"({product_pct_for_80:.2f}% of sold products) "
                "were required to reach approximately "
                "80% of product revenue."
            ),
        }
    )

    high_revenue_high_returns = (
        risk_products.loc[
            risk_products[
                "BusinessFlag"
            ]
            == "High Revenue / High Returns"
        ]
    )

    observations.append(
        {
            "Area": "Product Risk",
            "Observation": (
                f"{len(high_revenue_high_returns)} products "
                "combined above-median revenue with "
                "upper-quartile return rates."
            ),
        }
    )

    observations_df = (
        pd.DataFrame(
            observations
        )
    )

    save_csv(
        observations_df,
        OUTPUT_DIR
        / "business_observations.csv",
    )

    print(
        "\nBusiness Observations:"
    )

    print(
        observations_df.to_string(
            index=False
        )
    )

    print()
    print("-" * 78)
    print(
        "EDA 03: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()