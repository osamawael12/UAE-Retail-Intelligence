"""
UAE Retail Intelligence Platform
EDA 07 - Promotions & Discount Analysis

Analysis:
- Promoted vs non-promoted sales
- Promotion adoption
- Promotion type performance
- Campaign performance
- Discount depth analysis
- Revenue / units / margin relationships
- Seasonal campaign analysis
- Promotion efficiency flags

Important:
Results describe observed associations in the synthetic data.
They should not be interpreted as causal estimates.

Outputs:
assets/eda/07_promotions/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.data_access import (
    get_sales_detail,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/07_promotions"
)


def prepare_sales(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    data = sales.copy()

    data[
        "IsPromoted"
    ] = (
        data[
            "PromotionId"
        ].notna()
    ).astype(int)

    data[
        "PromotionStatus"
    ] = np.where(
        data[
            "IsPromoted"
        ]
        == 1,
        "Promoted",
        "Non-Promoted",
    )

    data[
        "DiscountRatePct"
    ] = np.where(
        data[
            "GrossSales"
        ]
        > 0,
        (
            data[
                "DiscountAmount"
            ]
            / data[
                "GrossSales"
            ]
            * 100
        ),
        0,
    )

    data[
        "GrossMarginPct"
    ] = np.where(
        data[
            "Revenue"
        ]
        != 0,
        (
            data[
                "GrossProfit"
            ]
            / data[
                "Revenue"
            ]
            * 100
        ),
        np.nan,
    )

    data[
        "DiscountBand"
    ] = pd.cut(
        data[
            "DiscountRatePct"
        ],
        bins=[
            -0.001,
            0.001,
            10,
            20,
            30,
            np.inf,
        ],
        labels=[
            "No Discount",
            "0-10%",
            "10-20%",
            "20-30%",
            "30%+",
        ],
        include_lowest=True,
    )

    return data


def build_promotion_status_summary(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales.groupby(
            "PromotionStatus",
            as_index=False,
        )
        .agg(
            SalesLines=(
                "OrderItemId",
                "count",
            ),
            Orders=(
                "OrderId",
                "nunique",
            ),
            GrossUnits=(
                "GrossUnits",
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
        "AverageRevenuePerLine"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "SalesLines"
        ]
    )

    summary[
        "AverageUnitsPerLine"
    ] = (
        summary[
            "GrossUnits"
        ]
        / summary[
            "SalesLines"
        ]
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

    return summary


def build_promotion_type_summary(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    promoted = (
        sales.loc[
            sales[
                "IsPromoted"
            ]
            == 1
        ]
    )

    summary = (
        promoted.groupby(
            "PromotionType",
            as_index=False,
        )
        .agg(
            Campaigns=(
                "PromotionId",
                "nunique",
            ),
            SalesLines=(
                "OrderItemId",
                "count",
            ),
            Orders=(
                "OrderId",
                "nunique",
            ),
            GrossUnits=(
                "GrossUnits",
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

    summary[
        "RevenuePerCampaign"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "Campaigns"
        ]
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


def build_campaign_summary(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    promoted = (
        sales.loc[
            sales[
                "IsPromoted"
            ]
            == 1
        ]
        .copy()
    )

    summary = (
        promoted.groupby(
            [
                "PromotionId",
                "PromotionCode",
                "PromotionName",
                "PromotionType",
            ],
            as_index=False,
        )
        .agg(
            SalesLines=(
                "OrderItemId",
                "count",
            ),
            Orders=(
                "OrderId",
                "nunique",
            ),
            Customers=(
                "CustomerId",
                "nunique",
            ),
            GrossUnits=(
                "GrossUnits",
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
        "RevenuePerOrder"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "Orders"
        ].replace(
            0,
            np.nan,
        )
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


def build_discount_band_summary(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales.groupby(
            "DiscountBand",
            observed=True,
            as_index=False,
        )
        .agg(
            SalesLines=(
                "OrderItemId",
                "count",
            ),
            GrossUnits=(
                "GrossUnits",
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

    summary[
        "AverageRevenuePerLine"
    ] = (
        summary[
            "Revenue"
        ]
        / summary[
            "SalesLines"
        ]
    )

    return summary


def build_monthly_promotion_trend(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    data = sales.copy()

    data[
        "MonthStart"
    ] = (
        data[
            "FullDate"
        ]
        .dt.to_period(
            "M"
        )
        .dt.to_timestamp()
    )

    summary = (
        data.groupby(
            [
                "MonthStart",
                "PromotionStatus",
            ],
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
            SalesLines=(
                "OrderItemId",
                "count",
            ),
        )
    )

    return summary


def main() -> None:
    configure_visuals()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print(
        "EDA 07 - PROMOTIONS & DISCOUNTS"
    )
    print("=" * 78)

    sales = prepare_sales(
        get_sales_detail()
    )

    promoted = (
        sales.loc[
            sales[
                "IsPromoted"
            ]
            == 1
        ]
    )

    # ========================================================
    # Promotion adoption
    # ========================================================

    promoted_lines = int(
        (
            sales[
                "IsPromoted"
            ]
            == 1
        ).sum()
    )

    total_lines = len(
        sales
    )

    adoption_rate = (
        promoted_lines
        / total_lines
        * 100
    )

    orders_with_promotion = int(
        promoted[
            "OrderId"
        ].nunique()
    )

    total_orders = int(
        sales[
            "OrderId"
        ].nunique()
    )

    order_promotion_rate = (
        orders_with_promotion
        / total_orders
        * 100
    )

    promotion_kpis = pd.DataFrame(
        [
            {
                "Metric":
                    "Sales Lines",
                "Value":
                    total_lines,
            },
            {
                "Metric":
                    "Promoted Sales Lines",
                "Value":
                    promoted_lines,
            },
            {
                "Metric":
                    "Promotion Line Adoption %",
                "Value":
                    adoption_rate,
            },
            {
                "Metric":
                    "Orders",
                "Value":
                    total_orders,
            },
            {
                "Metric":
                    "Orders with Promotion",
                "Value":
                    orders_with_promotion,
            },
            {
                "Metric":
                    "Order Promotion Adoption %",
                "Value":
                    order_promotion_rate,
            },
            {
                "Metric":
                    "Distinct Promotions Used",
                "Value":
                    promoted[
                        "PromotionId"
                    ].nunique(),
            },
        ]
    )

    save_csv(
        promotion_kpis,
        OUTPUT_DIR
        / "promotion_kpis.csv",
    )

    print(
        "\nPromotion KPIs:"
    )

    print(
        promotion_kpis.round(
            2
        ).to_string(
            index=False
        )
    )

    # ========================================================
    # Promoted vs non-promoted
    # ========================================================

    status_summary = (
        build_promotion_status_summary(
            sales
        )
    )

    save_csv(
        status_summary,
        OUTPUT_DIR
        / "promoted_vs_non_promoted.csv",
    )

    print(
        "\nPromoted vs Non-Promoted:"
    )

    print(
        status_summary.round(
            2
        ).to_string(
            index=False
        )
    )

    status_long = (
        status_summary[
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
            value_name="Value",
        )
    )

    plt.figure(
        figsize=(
            10,
            6,
        )
    )

    axis = sns.barplot(
        data=status_long,
        x="PromotionStatus",
        y="Value",
        hue="Metric",
    )

    plt.title(
        "Promoted vs Non-Promoted Revenue and Profit"
    )

    plt.xlabel(
        ""
    )

    plt.ylabel(
        "AED"
    )

    format_aed_axis(
        axis,
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "promoted_vs_non_promoted.png"
    )

    # ========================================================
    # Promotion Type
    # ========================================================

    type_summary = (
        build_promotion_type_summary(
            sales
        )
    )

    save_csv(
        type_summary,
        OUTPUT_DIR
        / "promotion_type_summary.csv",
    )

    plt.figure(
        figsize=(
            11,
            6,
        )
    )

    axis = sns.barplot(
        data=type_summary,
        y="PromotionType",
        x="Revenue",
        color="#7C3AED",
    )

    plt.title(
        "Revenue by Promotion Type"
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
        / "promotion_type_revenue.png"
    )

    # ========================================================
    # Campaign Performance
    # ========================================================

    campaigns = (
        build_campaign_summary(
            sales
        )
    )

    save_csv(
        campaigns,
        OUTPUT_DIR
        / "campaign_performance.csv",
    )

    top_campaigns = (
        campaigns.head(
            20
        )
    )

    plt.figure(
        figsize=(
            14,
            9,
        )
    )

    axis = sns.barplot(
        data=top_campaigns,
        y="PromotionName",
        x="Revenue",
        hue="PromotionType",
        dodge=False,
    )

    plt.title(
        "Top 20 Promotion Campaigns by Revenue"
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

    plt.legend(
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "top_campaigns_revenue.png"
    )

    # ========================================================
    # Discount bands
    # ========================================================

    discount_bands = (
        build_discount_band_summary(
            sales
        )
    )

    save_csv(
        discount_bands,
        OUTPUT_DIR
        / "discount_band_summary.csv",
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.lineplot(
        data=discount_bands,
        x="DiscountBand",
        y="GrossMarginPct",
        marker="o",
        linewidth=2.5,
        color="#DC2626",
    )

    plt.title(
        "Gross Margin by Discount Depth"
    )

    plt.xlabel(
        "Discount Band"
    )

    plt.ylabel(
        "Gross Margin (%)"
    )

    plt.xticks(
        rotation=25
    )

    save_figure(
        OUTPUT_DIR
        / "margin_by_discount_band.png"
    )

    # ========================================================
    # Discount vs Margin relationship
    # ========================================================

    campaign_plot = (
        campaigns.loc[
            campaigns[
                "SalesLines"
            ]
            >= 20
        ]
    )

    plt.figure(
        figsize=(
            12,
            8,
        )
    )

    sns.scatterplot(
        data=campaign_plot,
        x="DiscountRatePct",
        y="GrossMarginPct",
        hue="PromotionType",
        size="Revenue",
        sizes=(
            40,
            400,
        ),
        alpha=0.8,
    )

    plt.title(
        "Campaign Discount Rate vs Gross Margin"
    )

    plt.xlabel(
        "Effective Discount Rate (%)"
    )

    plt.ylabel(
        "Gross Margin (%)"
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
        / "discount_vs_margin.png"
    )

    # ========================================================
    # Discount vs Revenue per line
    # ========================================================

    discount_line_summary = (
        sales.groupby(
            "DiscountBand",
            observed=True,
            as_index=False,
        )
        .agg(
            SalesLines=(
                "OrderItemId",
                "count",
            ),
            AvgRevenuePerLine=(
                "Revenue",
                "mean",
            ),
            AvgGrossProfitPerLine=(
                "GrossProfit",
                "mean",
            ),
            AvgUnitsPerLine=(
                "GrossUnits",
                "mean",
            ),
        )
    )

    save_csv(
        discount_line_summary,
        OUTPUT_DIR
        / "discount_line_behavior.csv",
    )

    # ========================================================
    # Monthly promotion trend
    # ========================================================

    monthly = (
        build_monthly_promotion_trend(
            sales
        )
    )

    save_csv(
        monthly,
        OUTPUT_DIR
        / "monthly_promotion_trend.csv",
    )

    plt.figure(
        figsize=(
            15,
            7,
        )
    )

    axis = sns.lineplot(
        data=monthly,
        x="MonthStart",
        y="Revenue",
        hue="PromotionStatus",
        marker="o",
    )

    plt.title(
        "Monthly Revenue: Promoted vs Non-Promoted Sales"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Revenue"
    )

    format_aed_axis(
        axis,
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "monthly_promotion_revenue.png"
    )

    # ========================================================
    # Seasonal campaigns
    # ========================================================

    seasonal = (
        campaigns.loc[
            campaigns[
                "PromotionType"
            ]
            == "SEASONAL"
        ]
        .copy()
    )

    save_csv(
        seasonal,
        OUTPUT_DIR
        / "seasonal_campaigns.csv",
    )

    if not seasonal.empty:
        plt.figure(
            figsize=(
                14,
                8,
            )
        )

        axis = sns.barplot(
            data=seasonal.sort_values(
                "Revenue",
                ascending=False,
            ),
            y="PromotionName",
            x="Revenue",
            color="#0F766E",
        )

        plt.title(
            "Seasonal Campaign Revenue"
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
            / "seasonal_campaign_revenue.png"
        )

    # ========================================================
    # Campaign Efficiency Flags
    # ========================================================

    median_revenue = float(
        campaigns[
            "Revenue"
        ].median()
    )

    median_margin = float(
        campaigns[
            "GrossMarginPct"
        ].median()
    )

    margin_q25 = float(
        campaigns[
            "GrossMarginPct"
        ].quantile(
            0.25
        )
    )

    return_q75 = float(
        campaigns[
            "ReturnRatePct"
        ].quantile(
            0.75
        )
    )

    campaigns_flagged = (
        campaigns.copy()
    )

    campaigns_flagged[
        "BusinessFlag"
    ] = np.select(
        [
            (
                campaigns_flagged[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                campaigns_flagged[
                    "GrossMarginPct"
                ]
                <= margin_q25
            ),

            (
                campaigns_flagged[
                    "ReturnRatePct"
                ]
                >= return_q75
            ),

            (
                campaigns_flagged[
                    "Revenue"
                ]
                >= median_revenue
            )
            & (
                campaigns_flagged[
                    "GrossMarginPct"
                ]
                >= median_margin
            ),
        ],
        [
            "High Revenue / Margin Pressure",
            "High Return Rate",
            "High Revenue / Healthy Margin",
        ],
        default="Normal",
    )

    save_csv(
        campaigns_flagged,
        OUTPUT_DIR
        / "campaign_business_flags.csv",
    )

    # ========================================================
    # Correlation exploration
    # ========================================================

    correlation_columns = [
        "DiscountRatePct",
        "Revenue",
        "GrossProfit",
        "GrossMarginPct",
        "GrossUnits",
        "ReturnRatePct",
        "RevenuePerOrder",
    ]

    campaign_correlation = (
        campaigns[
            correlation_columns
        ]
        .corr()
    )

    campaign_correlation.to_csv(
        OUTPUT_DIR
        / "campaign_correlation_matrix.csv",
        encoding="utf-8-sig",
    )

    plt.figure(
        figsize=(
            9,
            7,
        )
    )

    sns.heatmap(
        campaign_correlation,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
    )

    plt.title(
        "Promotion Campaign Correlation Matrix"
    )

    save_figure(
        OUTPUT_DIR
        / "campaign_correlation_heatmap.png"
    )

    # ========================================================
    # Observations
    # ========================================================

    observations = []

    observations.append(
        {
            "Area":
                "Promotion Adoption",

            "Observation":
                (
                    f"{adoption_rate:.2f}% of sales lines "
                    "used a promotion, while "
                    f"{order_promotion_rate:.2f}% of orders "
                    "contained at least one promoted line."
                ),
        }
    )

    promoted_row = (
        status_summary.loc[
            status_summary[
                "PromotionStatus"
            ]
            == "Promoted"
        ]
    )

    non_promoted_row = (
        status_summary.loc[
            status_summary[
                "PromotionStatus"
            ]
            == "Non-Promoted"
        ]
    )

    if (
        not promoted_row.empty
        and not non_promoted_row.empty
    ):
        promoted_row = (
            promoted_row.iloc[0]
        )

        non_promoted_row = (
            non_promoted_row.iloc[0]
        )

        observations.append(
            {
                "Area":
                    "Margin",

                "Observation":
                    (
                        "Promoted sales lines had an aggregate "
                        f"gross margin of "
                        f"{float(promoted_row['GrossMarginPct']):.2f}% "
                        "versus "
                        f"{float(non_promoted_row['GrossMarginPct']):.2f}% "
                        "for non-promoted lines."
                    ),
            }
        )

        observations.append(
            {
                "Area":
                    "Basket Behaviour",

                "Observation":
                    (
                        "Average units per promoted sales line "
                        f"were "
                        f"{float(promoted_row['AverageUnitsPerLine']):.2f} "
                        "versus "
                        f"{float(non_promoted_row['AverageUnitsPerLine']):.2f} "
                        "for non-promoted lines."
                    ),
            }
        )

    if not type_summary.empty:
        top_type = (
            type_summary.iloc[0]
        )

        observations.append(
            {
                "Area":
                    "Promotion Type",

                "Observation":
                    (
                        f"{top_type['PromotionType']} campaigns "
                        "generated the largest aggregate promoted "
                        f"revenue at AED "
                        f"{float(top_type['Revenue']):,.2f}."
                    ),
            }
        )

    if not campaigns.empty:
        highest_revenue_campaign = (
            campaigns.iloc[0]
        )

        observations.append(
            {
                "Area":
                    "Campaign",

                "Observation":
                    (
                        f"{highest_revenue_campaign['PromotionName']} "
                        "generated the highest observed campaign "
                        f"revenue at AED "
                        f"{float(highest_revenue_campaign['Revenue']):,.2f}."
                    ),
            }
        )

    pressured = (
        campaigns_flagged.loc[
            campaigns_flagged[
                "BusinessFlag"
            ]
            == "High Revenue / Margin Pressure"
        ]
    )

    observations.append(
        {
            "Area":
                "Campaign Risk",

            "Observation":
                (
                    f"{len(pressured)} campaigns combined "
                    "above-median revenue with bottom-quartile "
                    "gross margin and should be reviewed for "
                    "promotion efficiency."
                ),
        }
    )

    observations.append(
        {
            "Area":
                "Interpretation",

            "Observation":
                (
                    "Promotion comparisons are descriptive "
                    "associations. Seasonality, product mix and "
                    "customer selection may also explain observed "
                    "differences; results should not be interpreted "
                    "as causal effects."
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
        "EDA 07: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()