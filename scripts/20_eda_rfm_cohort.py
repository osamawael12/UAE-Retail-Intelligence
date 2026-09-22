"""
UAE Retail Intelligence Platform
EDA 05 - RFM & Cohort Analysis

Purpose:
- Independently calculate RFM in Python.
- Segment customers using transaction-derived behaviour.
- Analyze segment size and revenue contribution.
- Build acquisition cohorts.
- Calculate monthly retention.
- Produce cohort retention heatmap.
- Cross-check customer analytics independently from SQL RFM.

Outputs:
assets/eda/05_rfm_cohort/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.data_access import (
    get_customer_360,
    get_sales_detail,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/05_rfm_cohort"
)


REFERENCE_DATE = pd.Timestamp(
    "2025-12-31"
)


def calculate_rfm(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate RFM values and quintile scores from Customer360.

    R Score:
    Higher score = more recent customer.

    F Score:
    Higher score = more frequent customer.

    M Score:
    Higher score = higher monetary value.
    """

    rfm = (
        customers.loc[
            customers[
                "Orders"
            ]
            > 0,
            [
                "CustomerId",
                "CustomerCode",
                "Orders",
                "Revenue",
                "FirstPurchaseDate",
                "LastPurchaseDate",
            ],
        ]
        .copy()
    )

    rfm[
        "LastPurchaseDate"
    ] = pd.to_datetime(
        rfm[
            "LastPurchaseDate"
        ]
    )

    rfm[
        "Recency"
    ] = (
        REFERENCE_DATE
        - rfm[
            "LastPurchaseDate"
        ]
    ).dt.days

    rfm[
        "Frequency"
    ] = (
        pd.to_numeric(
            rfm[
                "Orders"
            ]
        )
        .astype(int)
    )

    rfm[
        "Monetary"
    ] = pd.to_numeric(
        rfm[
            "Revenue"
        ]
    )

    # rank(method="first") ensures qcut receives
    # unique ranking positions even with many tied values.
    recency_rank = (
        rfm[
            "Recency"
        ]
        .rank(
            method="first",
            ascending=False,
        )
    )

    frequency_rank = (
        rfm[
            "Frequency"
        ]
        .rank(
            method="first",
            ascending=True,
        )
    )

    monetary_rank = (
        rfm[
            "Monetary"
        ]
        .rank(
            method="first",
            ascending=True,
        )
    )

    rfm[
        "RScore"
    ] = (
        pd.qcut(
            recency_rank,
            q=5,
            labels=[
                1,
                2,
                3,
                4,
                5,
            ],
        )
        .astype(int)
    )

    rfm[
        "FScore"
    ] = (
        pd.qcut(
            frequency_rank,
            q=5,
            labels=[
                1,
                2,
                3,
                4,
                5,
            ],
        )
        .astype(int)
    )

    rfm[
        "MScore"
    ] = (
        pd.qcut(
            monetary_rank,
            q=5,
            labels=[
                1,
                2,
                3,
                4,
                5,
            ],
        )
        .astype(int)
    )

    rfm[
        "RFMCode"
    ] = (
        rfm[
            "RScore"
        ].astype(str)
        + rfm[
            "FScore"
        ].astype(str)
        + rfm[
            "MScore"
        ].astype(str)
    )

    rfm[
        "RFMTotalScore"
    ] = (
        rfm[
            "RScore"
        ]
        + rfm[
            "FScore"
        ]
        + rfm[
            "MScore"
        ]
    )

    rfm[
        "RFMSegment"
    ] = rfm.apply(
        classify_rfm_segment,
        axis=1,
    )

    return rfm


def classify_rfm_segment(
    row: pd.Series,
) -> str:
    r = int(
        row[
            "RScore"
        ]
    )

    f = int(
        row[
            "FScore"
        ]
    )

    m = int(
        row[
            "MScore"
        ]
    )

    if (
        r >= 4
        and f >= 4
        and m >= 4
    ):
        return "Champions"

    if (
        r >= 3
        and f >= 4
    ):
        return "Loyal"

    if (
        r >= 4
        and f in {
            2,
            3,
        }
    ):
        return (
            "Potential Loyalists"
        )

    if (
        r == 5
        and f == 1
    ):
        return "New Customers"

    if (
        r <= 2
        and f >= 3
    ):
        return "At Risk"

    if (
        r == 1
        and f <= 2
    ):
        return "Lost"

    return "Regular"


def build_rfm_segment_summary(
    rfm: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        rfm.groupby(
            "RFMSegment",
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
            AvgRecency=(
                "Recency",
                "mean",
            ),
            AvgFrequency=(
                "Frequency",
                "mean",
            ),
            AvgMonetary=(
                "Monetary",
                "mean",
            ),
            AvgRFMScore=(
                "RFMTotalScore",
                "mean",
            ),
        )
    )

    summary[
        "CustomerPct"
    ] = (
        summary[
            "Customers"
        ]
        / summary[
            "Customers"
        ].sum()
        * 100
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


def build_customer_month_activity(
    sales_detail: pd.DataFrame,
) -> pd.DataFrame:
    """
    One Customer x Month row.

    SalesDetail contains multiple products per order, so we
    deduplicate customer-month activity before cohort logic.
    """

    activity = (
        sales_detail[
            [
                "CustomerId",
                "FullDate",
            ]
        ]
        .copy()
    )

    activity[
        "FullDate"
    ] = pd.to_datetime(
        activity[
            "FullDate"
        ]
    )

    activity[
        "ActivityMonth"
    ] = (
        activity[
            "FullDate"
        ]
        .dt.to_period(
            "M"
        )
        .dt.to_timestamp()
    )

    return (
        activity[
            [
                "CustomerId",
                "ActivityMonth",
            ]
        ]
        .drop_duplicates()
        .reset_index(
            drop=True
        )
    )


def calculate_cohort_retention(
    sales_detail: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    activity = (
        build_customer_month_activity(
            sales_detail
        )
    )

    first_purchase = (
        activity.groupby(
            "CustomerId",
            as_index=False,
        )[
            "ActivityMonth"
        ]
        .min()
        .rename(
            columns={
                "ActivityMonth":
                    "CohortMonth"
            }
        )
    )

    cohort_data = (
        activity.merge(
            first_purchase,
            on="CustomerId",
            how="inner",
            validate="many_to_one",
        )
    )

    cohort_data[
        "CohortIndex"
    ] = (
        (
            cohort_data[
                "ActivityMonth"
            ].dt.year
            - cohort_data[
                "CohortMonth"
            ].dt.year
        )
        * 12
        +
        (
            cohort_data[
                "ActivityMonth"
            ].dt.month
            - cohort_data[
                "CohortMonth"
            ].dt.month
        )
    )

    cohort_counts = (
        cohort_data.groupby(
            [
                "CohortMonth",
                "CohortIndex",
            ],
            as_index=False,
        )
        .agg(
            ActiveCustomers=(
                "CustomerId",
                "nunique",
            )
        )
    )

    cohort_sizes = (
        first_purchase.groupby(
            "CohortMonth",
            as_index=False,
        )
        .agg(
            CohortSize=(
                "CustomerId",
                "nunique",
            )
        )
    )

    cohort_counts = (
        cohort_counts.merge(
            cohort_sizes,
            on="CohortMonth",
            how="left",
            validate="many_to_one",
        )
    )

    cohort_counts[
        "RetentionPct"
    ] = (
        cohort_counts[
            "ActiveCustomers"
        ]
        / cohort_counts[
            "CohortSize"
        ]
        * 100
    )

    retention_matrix = (
        cohort_counts.pivot(
            index="CohortMonth",
            columns="CohortIndex",
            values="RetentionPct",
        )
        .sort_index()
    )

    return (
        cohort_counts,
        retention_matrix,
    )


def build_cohort_revenue(
    sales_detail: pd.DataFrame,
) -> pd.DataFrame:
    customer_first_purchase = (
        sales_detail.groupby(
            "CustomerId",
            as_index=False,
        )[
            "FullDate"
        ]
        .min()
    )

    customer_first_purchase[
        "CohortMonth"
    ] = (
        pd.to_datetime(
            customer_first_purchase[
                "FullDate"
            ]
        )
        .dt.to_period(
            "M"
        )
        .dt.to_timestamp()
    )

    customer_revenue = (
        sales_detail.groupby(
            "CustomerId",
            as_index=False,
        )
        .agg(
            Revenue=(
                "Revenue",
                "sum",
            )
        )
    )

    cohort_revenue = (
        customer_first_purchase[
            [
                "CustomerId",
                "CohortMonth",
            ]
        ]
        .merge(
            customer_revenue,
            on="CustomerId",
            how="inner",
            validate="one_to_one",
        )
    )

    summary = (
        cohort_revenue.groupby(
            "CohortMonth",
            as_index=False,
        )
        .agg(
            Customers=(
                "CustomerId",
                "nunique",
            ),
            LifetimeRevenue=(
                "Revenue",
                "sum",
            ),
            AvgLifetimeRevenue=(
                "Revenue",
                "mean",
            ),
        )
    )

    summary[
        "RevenueContributionPct"
    ] = (
        summary[
            "LifetimeRevenue"
        ]
        / summary[
            "LifetimeRevenue"
        ].sum()
        * 100
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
        "EDA 05 - RFM & COHORT ANALYSIS"
    )
    print("=" * 78)

    customers = (
        get_customer_360()
    )

    sales_detail = (
        get_sales_detail()
    )

    # ========================================================
    # RFM
    # ========================================================

    rfm = calculate_rfm(
        customers
    )

    rfm_summary = (
        build_rfm_segment_summary(
            rfm
        )
    )

    save_csv(
        rfm,
        OUTPUT_DIR
        / "rfm_customer_scores.csv",
    )

    save_csv(
        rfm_summary,
        OUTPUT_DIR
        / "rfm_segment_summary.csv",
    )

    print(
        "\nRFM Segment Summary:"
    )

    print(
        rfm_summary[
            [
                "RFMSegment",
                "Customers",
                "CustomerPct",
                "Revenue",
                "RevenueContributionPct",
                "AvgRecency",
                "AvgFrequency",
                "AvgMonetary",
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
    # RFM segment size
    # ========================================================

    segment_order = (
        rfm_summary.sort_values(
            "Customers",
            ascending=False,
        )
    )

    plt.figure(
        figsize=(
            13,
            7,
        )
    )

    sns.barplot(
        data=segment_order,
        y="RFMSegment",
        x="Customers",
        color="#2563EB",
    )

    plt.title(
        "RFM Customer Segment Size"
    )

    plt.xlabel(
        "Customers"
    )

    plt.ylabel(
        ""
    )

    save_figure(
        OUTPUT_DIR
        / "rfm_segment_size.png"
    )

    # ========================================================
    # Segment revenue
    # ========================================================

    revenue_order = (
        rfm_summary.sort_values(
            "Revenue",
            ascending=False,
        )
    )

    plt.figure(
        figsize=(
            13,
            7,
        )
    )

    axis = sns.barplot(
        data=revenue_order,
        y="RFMSegment",
        x="Revenue",
        color="#7C3AED",
    )

    plt.title(
        "Revenue by RFM Segment"
    )

    plt.xlabel(
        "Lifetime Revenue"
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
        / "rfm_segment_revenue.png"
    )

    # ========================================================
    # Recency vs Frequency
    # ========================================================

    sample_size = min(
        12_000,
        len(rfm),
    )

    rfm_sample = (
        rfm.sample(
            n=sample_size,
            random_state=42,
        )
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sns.scatterplot(
        data=rfm_sample,
        x="Recency",
        y="Frequency",
        hue="RFMSegment",
        size="Monetary",
        sizes=(
            10,
            150,
        ),
        alpha=0.45,
    )

    plt.title(
        "RFM: Recency vs Frequency"
    )

    plt.xlabel(
        "Recency (Days)"
    )

    plt.ylabel(
        "Frequency (Orders)"
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
        / "rfm_recency_frequency.png"
    )

    # ========================================================
    # RFM score heatmap
    # ========================================================

    score_matrix = (
        rfm.pivot_table(
            index="RScore",
            columns="FScore",
            values="Monetary",
            aggfunc="mean",
        )
        .sort_index(
            ascending=False
        )
    )

    score_matrix.to_csv(
        OUTPUT_DIR
        / "rf_score_monetary_matrix.csv",
        encoding="utf-8-sig",
    )

    plt.figure(
        figsize=(
            9,
            7,
        )
    )

    sns.heatmap(
        score_matrix,
        annot=True,
        fmt=".0f",
        cmap="YlGnBu",
    )

    plt.title(
        "Average Monetary Value by R/F Score"
    )

    plt.xlabel(
        "Frequency Score"
    )

    plt.ylabel(
        "Recency Score"
    )

    save_figure(
        OUTPUT_DIR
        / "rf_score_heatmap.png"
    )

    # ========================================================
    # Cohort Retention
    # ========================================================

    (
        cohort_long,
        retention_matrix,
    ) = (
        calculate_cohort_retention(
            sales_detail
        )
    )

    cohort_long_output = (
        cohort_long.copy()
    )

    cohort_long_output[
        "CohortMonth"
    ] = (
        cohort_long_output[
            "CohortMonth"
        ].dt.strftime(
            "%Y-%m"
        )
    )

    save_csv(
        cohort_long_output,
        OUTPUT_DIR
        / "cohort_retention_long.csv",
    )

    matrix_output = (
        retention_matrix.copy()
    )

    matrix_output.index = (
        matrix_output.index.strftime(
            "%Y-%m"
        )
    )

    matrix_output.to_csv(
        OUTPUT_DIR
        / "cohort_retention_matrix.csv",
        encoding="utf-8-sig",
    )

    # Limit displayed heatmap to first 12 months.
    heatmap_matrix = (
        retention_matrix.loc[
            :,
            [
                column
                for column
                in retention_matrix.columns
                if column <= 12
            ],
        ]
        .copy()
    )

    heatmap_matrix.index = (
        heatmap_matrix.index.strftime(
            "%Y-%m"
        )
    )

    plt.figure(
        figsize=(
            16,
            12,
        )
    )

    sns.heatmap(
        heatmap_matrix,
        annot=True,
        fmt=".1f",
        cmap="Blues",
        vmin=0,
        vmax=100,
        linewidths=0.3,
        cbar_kws={
            "label":
                "Retention (%)"
        },
    )

    plt.title(
        "Customer Cohort Retention Heatmap"
    )

    plt.xlabel(
        "Months Since First Purchase"
    )

    plt.ylabel(
        "Acquisition Cohort"
    )

    save_figure(
        OUTPUT_DIR
        / "cohort_retention_heatmap.png"
    )

    # ========================================================
    # Retention curves
    # ========================================================

    selected_cohorts = (
        retention_matrix
        .index[
            ::6
        ]
    )

    plt.figure(
        figsize=(
            13,
            7,
        )
    )

    for cohort in (
        selected_cohorts
    ):
        values = (
            retention_matrix.loc[
                cohort
            ]
            .dropna()
        )

        values = (
            values.loc[
                values.index
                <= 12
            ]
        )

        plt.plot(
            values.index,
            values.values,
            marker="o",
            linewidth=1.5,
            label=(
                cohort.strftime(
                    "%Y-%m"
                )
            ),
        )

    plt.title(
        "Selected Cohort Retention Curves"
    )

    plt.xlabel(
        "Months Since Acquisition"
    )

    plt.ylabel(
        "Retention (%)"
    )

    plt.xticks(
        range(
            0,
            13,
        )
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
        / "cohort_retention_curves.png"
    )

    # ========================================================
    # Cohort Revenue
    # ========================================================

    cohort_revenue = (
        build_cohort_revenue(
            sales_detail
        )
    )

    cohort_revenue_output = (
        cohort_revenue.copy()
    )

    cohort_revenue_output[
        "CohortMonth"
    ] = (
        cohort_revenue_output[
            "CohortMonth"
        ].dt.strftime(
            "%Y-%m"
        )
    )

    save_csv(
        cohort_revenue_output,
        OUTPUT_DIR
        / "cohort_revenue.csv",
    )

    plt.figure(
        figsize=(
            15,
            7,
        )
    )

    axis = sns.barplot(
        data=cohort_revenue,
        x="CohortMonth",
        y="LifetimeRevenue",
        color="#0F766E",
    )

    plt.title(
        "Lifetime Revenue by Acquisition Cohort"
    )

    plt.xlabel(
        "Cohort Month"
    )

    plt.ylabel(
        "Lifetime Revenue"
    )

    plt.xticks(
        rotation=90
    )

    format_aed_axis(
        axis,
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "cohort_lifetime_revenue.png"
    )

    # ========================================================
    # Cohort validation
    # ========================================================

    month_zero = (
        cohort_long.loc[
            cohort_long[
                "CohortIndex"
            ]
            == 0,
            "RetentionPct",
        ]
    )

    if not np.allclose(
        month_zero,
        100.0,
    ):
        raise RuntimeError(
            "Cohort validation failed: "
            "Month 0 retention must equal 100%."
        )

    # ========================================================
    # Business observations
    # ========================================================

    observations = []

    top_segment = (
        rfm_summary.sort_values(
            "Revenue",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area": "RFM",
            "Observation": (
                f"{top_segment['RFMSegment']} generated "
                f"the largest RFM-segment revenue at "
                f"AED {float(top_segment['Revenue']):,.2f}, "
                f"representing "
                f"{float(top_segment['RevenueContributionPct']):.2f}% "
                "of purchasing-customer revenue."
            ),
        }
    )

    at_risk = (
        rfm_summary.loc[
            rfm_summary[
                "RFMSegment"
            ]
            == "At Risk"
        ]
    )

    if not at_risk.empty:
        row = (
            at_risk.iloc[0]
        )

        observations.append(
            {
                "Area": "RFM",
                "Observation": (
                    f"{int(row['Customers']):,} customers "
                    "were classified as At Risk and represented "
                    f"{float(row['RevenueContributionPct']):.2f}% "
                    "of historical customer revenue."
                ),
            }
        )

    lost = (
        rfm_summary.loc[
            rfm_summary[
                "RFMSegment"
            ]
            == "Lost"
        ]
    )

    if not lost.empty:
        row = (
            lost.iloc[0]
        )

        observations.append(
            {
                "Area": "RFM",
                "Observation": (
                    f"{int(row['Customers']):,} customers "
                    "were classified as Lost."
                ),
            }
        )

    month_one = (
        cohort_long.loc[
            cohort_long[
                "CohortIndex"
            ]
            == 1
        ]
    )

    if not month_one.empty:
        weighted_m1 = (
            (
                month_one[
                    "ActiveCustomers"
                ].sum()
            )
            /
            (
                month_one[
                    "CohortSize"
                ].sum()
            )
            * 100
        )

        observations.append(
            {
                "Area": "Cohort",
                "Observation": (
                    "Weighted Month-1 retention across "
                    f"observable cohorts was {weighted_m1:.2f}%."
                ),
            }
        )

    mature_cohorts = (
        cohort_long.loc[
            cohort_long[
                "CohortIndex"
            ]
            == 6
        ]
    )

    if not mature_cohorts.empty:
        weighted_m6 = (
            mature_cohorts[
                "ActiveCustomers"
            ].sum()
            /
            mature_cohorts[
                "CohortSize"
            ].sum()
            * 100
        )

        observations.append(
            {
                "Area": "Cohort",
                "Observation": (
                    "Weighted Month-6 retention across "
                    f"observable cohorts was {weighted_m6:.2f}%."
                ),
            }
        )

    highest_value_cohort = (
        cohort_revenue.sort_values(
            "AvgLifetimeRevenue",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area": "Cohort",
            "Observation": (
                "The acquisition cohort with the highest "
                "average lifetime revenue per customer was "
                f"{highest_value_cohort['CohortMonth']:%Y-%m} "
                f"at AED "
                f"{float(highest_value_cohort['AvgLifetimeRevenue']):,.2f}."
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
        "EDA 05: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()