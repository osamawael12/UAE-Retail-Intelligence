"""
UAE Retail Intelligence Platform
EDA 04 - Customer Analysis

Analysis:
- Registered vs purchasing customers
- Repeat customer behaviour
- Orders per customer
- Revenue per customer
- AOV distribution
- Recency
- Customer value concentration
- New vs returning customers
- Preferred channel / emirate
- Customer purchasing lifecycle
- Hidden simulation persona validation

The hidden persona dataset is used only to validate that the
synthetic generator produced meaningful behavioural patterns.
It is not treated as an observed business attribute.

Outputs:
assets/eda/04_customer/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sqlalchemy import text

from config.generation_config import (
    CONFIG,
)
from src.analytics.data_access import (
    get_customer_360,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)
from src.database.connection import (
    get_engine,
)


OUTPUT_DIR = Path(
    "assets/eda/04_customer"
)


def get_monthly_customer_activity() -> pd.DataFrame:
    """
    Calculate monthly active/new/returning customers in SQL.

    A customer is new in the month of their first-ever
    completed purchase.
    """

    query = text(
        """
        WITH FirstPurchase AS
        (
            SELECT
                CustomerId,

                DATEFROMPARTS(
                    YEAR(
                        MIN(
                            OrderDateTime
                        )
                    ),
                    MONTH(
                        MIN(
                            OrderDateTime
                        )
                    ),
                    1
                ) AS FirstPurchaseMonth

            FROM sales.SalesOrder

            WHERE
                OrderStatus
                = 'COMPLETED'

            GROUP BY
                CustomerId
        ),

        MonthlyActivity AS
        (
            SELECT DISTINCT
                CustomerId,

                DATEFROMPARTS(
                    YEAR(
                        OrderDateTime
                    ),
                    MONTH(
                        OrderDateTime
                    ),
                    1
                ) AS ActivityMonth

            FROM sales.SalesOrder

            WHERE
                OrderStatus
                = 'COMPLETED'
        )

        SELECT
            a.ActivityMonth,

            COUNT_BIG(*)
                AS ActiveCustomers,

            SUM(
                CASE
                    WHEN
                        f.FirstPurchaseMonth
                        = a.ActivityMonth
                        THEN 1
                    ELSE 0
                END
            ) AS NewCustomers,

            SUM(
                CASE
                    WHEN
                        f.FirstPurchaseMonth
                        < a.ActivityMonth
                        THEN 1
                    ELSE 0
                END
            ) AS ReturningCustomers

        FROM MonthlyActivity a

        INNER JOIN FirstPurchase f
            ON a.CustomerId
               = f.CustomerId

        GROUP BY
            a.ActivityMonth

        ORDER BY
            a.ActivityMonth
        """
    )

    dataframe = pd.read_sql_query(
        query,
        get_engine(),
    )

    dataframe[
        "ActivityMonth"
    ] = pd.to_datetime(
        dataframe[
            "ActivityMonth"
        ]
    )

    dataframe[
        "ReturningCustomerPct"
    ] = (
        dataframe[
            "ReturningCustomers"
        ]
        / dataframe[
            "ActiveCustomers"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    return dataframe


def build_customer_concentration(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    purchasing = (
        customers.loc[
            customers[
                "Orders"
            ]
            > 0
        ]
        .copy()
    )

    purchasing = (
        purchasing.sort_values(
            [
                "Revenue",
                "CustomerId",
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

    purchasing[
        "CustomerRank"
    ] = np.arange(
        1,
        len(purchasing) + 1,
    )

    total_revenue = float(
        purchasing[
            "Revenue"
        ].sum()
    )

    purchasing[
        "RevenueContributionPct"
    ] = (
        purchasing[
            "Revenue"
        ]
        / total_revenue
        * 100
    )

    purchasing[
        "CumulativeRevenuePct"
    ] = (
        purchasing[
            "Revenue"
        ].cumsum()
        / total_revenue
        * 100
    )

    purchasing[
        "CumulativeCustomerPct"
    ] = (
        purchasing[
            "CustomerRank"
        ]
        / len(purchasing)
        * 100
    )

    return purchasing


def validate_hidden_personas(
) -> pd.DataFrame:
    """
    Compare hidden simulation personas to actual transaction
    outcomes.

    This is generator validation only.
    """

    path = (
        CONFIG.output_directory
        / "customer_simulation_profiles.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    profiles = pd.read_csv(
        path
    )

    customers = (
        get_customer_360()
    )

    validation = (
        customers[
            [
                "CustomerId",
                "Orders",
                "Revenue",
                "AOV",
                "ReturnRatePct",
                "RecencyDays",
            ]
        ]
        .merge(
            profiles[
                [
                    "CustomerId",
                    "Persona",
                    "PurchasePropensity",
                    "PriceSensitivity",
                    "PromotionSensitivity",
                    "ReturnMultiplier",
                    "ExpectedBasketSize",
                ]
            ],
            on="CustomerId",
            how="inner",
            validate="one_to_one",
        )
    )

    summary = (
        validation.groupby(
            "Persona",
            as_index=False,
        )
        .agg(
            Customers=(
                "CustomerId",
                "count",
            ),
            AvgOrders=(
                "Orders",
                "mean",
            ),
            AvgRevenue=(
                "Revenue",
                "mean",
            ),
            AvgAOV=(
                "AOV",
                "mean",
            ),
            AvgRecency=(
                "RecencyDays",
                "mean",
            ),
            AvgReturnRate=(
                "ReturnRatePct",
                "mean",
            ),
            AvgPurchasePropensity=(
                "PurchasePropensity",
                "mean",
            ),
            AvgPromotionSensitivity=(
                "PromotionSensitivity",
                "mean",
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
        "EDA 04 - CUSTOMER ANALYSIS"
    )
    print("=" * 78)

    customers = (
        get_customer_360()
    )

    purchasing = (
        customers.loc[
            customers[
                "Orders"
            ]
            > 0
        ]
        .copy()
    )

    # ========================================================
    # Customer KPI summary
    # ========================================================

    registered_customers = (
        len(customers)
    )

    purchasing_customers = (
        len(purchasing)
    )

    repeat_customers = int(
        (
            purchasing[
                "Orders"
            ]
            >= 2
        ).sum()
    )

    one_time_customers = int(
        (
            purchasing[
                "Orders"
            ]
            == 1
        ).sum()
    )

    non_purchasing = (
        registered_customers
        - purchasing_customers
    )

    repeat_rate = (
        repeat_customers
        / purchasing_customers
        * 100
        if purchasing_customers
        else 0
    )

    purchase_frequency = (
        purchasing[
            "Orders"
        ].sum()
        / purchasing_customers
        if purchasing_customers
        else 0
    )

    kpis = pd.DataFrame(
        [
            {
                "Metric":
                    "Registered Customers",
                "Value":
                    registered_customers,
            },
            {
                "Metric":
                    "Purchasing Customers",
                "Value":
                    purchasing_customers,
            },
            {
                "Metric":
                    "Non-Purchasing Customers",
                "Value":
                    non_purchasing,
            },
            {
                "Metric":
                    "Repeat Customers",
                "Value":
                    repeat_customers,
            },
            {
                "Metric":
                    "One-Time Customers",
                "Value":
                    one_time_customers,
            },
            {
                "Metric":
                    "Repeat Customer Rate %",
                "Value":
                    repeat_rate,
            },
            {
                "Metric":
                    "Purchase Frequency",
                "Value":
                    purchase_frequency,
            },
            {
                "Metric":
                    "Avg Revenue per Purchasing Customer",
                "Value":
                    purchasing[
                        "Revenue"
                    ].mean(),
            },
        ]
    )

    save_csv(
        kpis,
        OUTPUT_DIR
        / "customer_kpis.csv",
    )

    print(
        "\nCustomer KPIs:"
    )

    print(
        kpis.round(
            2
        ).to_string(
            index=False
        )
    )

    # ========================================================
    # Orders per customer
    # ========================================================

    order_distribution = (
        purchasing[
            "Orders"
        ]
        .value_counts()
        .sort_index()
        .rename_axis(
            "Orders"
        )
        .reset_index(
            name="Customers"
        )
    )

    order_distribution[
        "CustomerPct"
    ] = (
        order_distribution[
            "Customers"
        ]
        / purchasing_customers
        * 100
    )

    save_csv(
        order_distribution,
        OUTPUT_DIR
        / "orders_per_customer.csv",
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=purchasing,
        x="Orders",
        discrete=True,
        color="#2563EB",
    )

    plt.title(
        "Orders per Purchasing Customer"
    )

    plt.xlabel(
        "Lifetime Orders"
    )

    plt.ylabel(
        "Customers"
    )

    save_figure(
        OUTPUT_DIR
        / "orders_per_customer.png"
    )

    # ========================================================
    # Revenue distribution
    # ========================================================

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=purchasing,
        x="Revenue",
        bins=60,
        kde=True,
        color="#7C3AED",
    )

    plt.title(
        "Customer Lifetime Revenue Distribution"
    )

    plt.xlabel(
        "Lifetime Revenue"
    )

    plt.ylabel(
        "Customers"
    )

    format_aed_axis(
        plt.gca(),
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "customer_revenue_distribution.png"
    )

    # ========================================================
    # AOV distribution
    # ========================================================

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=purchasing,
        x="AOV",
        bins=60,
        kde=True,
        color="#0F766E",
    )

    plt.title(
        "Customer Average Order Value Distribution"
    )

    plt.xlabel(
        "AOV"
    )

    plt.ylabel(
        "Customers"
    )

    format_aed_axis(
        plt.gca(),
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "customer_aov_distribution.png"
    )

    # ========================================================
    # Recency distribution
    # ========================================================

    recency = (
        purchasing.dropna(
            subset=[
                "RecencyDays"
            ]
        )
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=recency,
        x="RecencyDays",
        bins=50,
        kde=True,
        color="#EA580C",
    )

    plt.title(
        "Customer Purchase Recency"
    )

    plt.xlabel(
        "Days Since Last Purchase"
    )

    plt.ylabel(
        "Customers"
    )

    save_figure(
        OUTPUT_DIR
        / "customer_recency.png"
    )

    # ========================================================
    # Frequency vs Revenue
    # ========================================================

    plt.figure(
        figsize=(
            12,
            8,
        )
    )

    sns.scatterplot(
        data=purchasing,
        x="Orders",
        y="Revenue",
        hue="PreferredChannelName",
        size="AOV",
        sizes=(
            10,
            150,
        ),
        alpha=0.35,
    )

    plt.title(
        "Purchase Frequency vs Customer Revenue"
    )

    plt.xlabel(
        "Lifetime Orders"
    )

    plt.ylabel(
        "Lifetime Revenue"
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
        / "frequency_vs_revenue.png"
    )

    # ========================================================
    # New vs Returning
    # ========================================================

    monthly_activity = (
        get_monthly_customer_activity()
    )

    save_csv(
        monthly_activity,
        OUTPUT_DIR
        / "monthly_customer_activity.csv",
    )

    activity_long = (
        monthly_activity[
            [
                "ActivityMonth",
                "NewCustomers",
                "ReturningCustomers",
            ]
        ]
        .melt(
            id_vars=[
                "ActivityMonth"
            ],
            var_name="CustomerType",
            value_name="Customers",
        )
    )

    plt.figure(
        figsize=(
            15,
            7,
        )
    )

    sns.lineplot(
        data=activity_long,
        x="ActivityMonth",
        y="Customers",
        hue="CustomerType",
        marker="o",
    )

    plt.title(
        "New vs Returning Customers by Month"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Customers"
    )

    save_figure(
        OUTPUT_DIR
        / "new_vs_returning_customers.png"
    )

    # ========================================================
    # Preferred channel
    # ========================================================

    channel_summary = (
        customers.groupby(
            "PreferredChannelName",
            dropna=False,
            as_index=False,
        )
        .agg(
            RegisteredCustomers=(
                "CustomerId",
                "count",
            ),
            PurchasingCustomers=(
                "Orders",
                lambda values:
                    (
                        values > 0
                    ).sum(),
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
        )
    )

    save_csv(
        channel_summary,
        OUTPUT_DIR
        / "preferred_channel_summary.csv",
    )

    # ========================================================
    # Preferred emirate
    # ========================================================

    emirate_summary = (
        customers.groupby(
            "PreferredEmirateName",
            dropna=False,
            as_index=False,
        )
        .agg(
            Customers=(
                "CustomerId",
                "count",
            ),
            PurchasingCustomers=(
                "Orders",
                lambda values:
                    (
                        values > 0
                    ).sum(),
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
        )
        .sort_values(
            "Revenue",
            ascending=False,
        )
    )

    save_csv(
        emirate_summary,
        OUTPUT_DIR
        / "preferred_emirate_summary.csv",
    )

    # ========================================================
    # Customer value concentration
    # ========================================================

    concentration = (
        build_customer_concentration(
            customers
        )
    )

    save_csv(
        concentration[
            [
                "CustomerId",
                "CustomerCode",
                "Orders",
                "Revenue",
                "CustomerRank",
                "RevenueContributionPct",
                "CumulativeRevenuePct",
                "CumulativeCustomerPct",
            ]
        ],
        OUTPUT_DIR
        / "customer_revenue_concentration.csv",
    )

    plt.figure(
        figsize=(
            12,
            7,
        )
    )

    plt.plot(
        concentration[
            "CumulativeCustomerPct"
        ],
        concentration[
            "CumulativeRevenuePct"
        ],
        linewidth=2.5,
        color="#2563EB",
    )

    plt.axhline(
        80,
        color="#DC2626",
        linestyle="--",
        label="80% Revenue",
    )

    customer_80 = (
        concentration.loc[
            concentration[
                "CumulativeRevenuePct"
            ]
            >= 80
        ]
        .iloc[0]
    )

    pct_customers_for_80 = float(
        customer_80[
            "CumulativeCustomerPct"
        ]
    )

    plt.axvline(
        pct_customers_for_80,
        color="#0F766E",
        linestyle="--",
        label=(
            f"{pct_customers_for_80:.1f}% "
            "of Customers"
        ),
    )

    plt.title(
        "Customer Revenue Concentration"
    )

    plt.xlabel(
        "Cumulative Customers (%)"
    )

    plt.ylabel(
        "Cumulative Revenue (%)"
    )

    plt.legend()

    save_figure(
        OUTPUT_DIR
        / "customer_revenue_concentration.png"
    )

    # ========================================================
    # Top customers
    # ========================================================

    top_customers = (
        purchasing.sort_values(
            "Revenue",
            ascending=False,
        )
        .head(25)
    )

    save_csv(
        top_customers,
        OUTPUT_DIR
        / "top_25_customers.csv",
    )

    # ========================================================
    # Return behaviour
    # ========================================================

    customer_return_summary = (
        purchasing[
            [
                "CustomerId",
                "CustomerCode",
                "Orders",
                "Revenue",
                "ReturnRatePct",
            ]
        ]
        .sort_values(
            "ReturnRatePct",
            ascending=False,
        )
    )

    save_csv(
        customer_return_summary,
        OUTPUT_DIR
        / "customer_return_rates.csv",
    )

    # ========================================================
    # Hidden persona validation
    # ========================================================

    persona_validation = (
        validate_hidden_personas()
    )

    if not persona_validation.empty:
        save_csv(
            persona_validation,
            OUTPUT_DIR
            / "simulation_persona_validation.csv",
        )

        print(
            "\nSimulation Persona Validation:"
        )

        print(
            persona_validation.round(
                2
            ).to_string(
                index=False
            )
        )

    # ========================================================
    # Business observations
    # ========================================================

    observations = []

    observations.append(
        {
            "Area": "Engagement",
            "Observation": (
                f"{purchasing_customers:,} of "
                f"{registered_customers:,} registered customers "
                "made at least one completed purchase."
            ),
        }
    )

    observations.append(
        {
            "Area": "Retention",
            "Observation": (
                f"{repeat_rate:.2f}% of purchasing customers "
                "completed at least two orders."
            ),
        }
    )

    observations.append(
        {
            "Area": "Frequency",
            "Observation": (
                "Purchasing customers completed an average of "
                f"{purchase_frequency:.2f} orders each."
            ),
        }
    )

    observations.append(
        {
            "Area": "Concentration",
            "Observation": (
                f"Approximately {pct_customers_for_80:.2f}% "
                "of purchasing customers generated 80% "
                "of customer revenue."
            ),
        }
    )

    latest_month = (
        monthly_activity.iloc[-1]
    )

    observations.append(
        {
            "Area": "Customer Mix",
            "Observation": (
                f"In {latest_month['ActivityMonth']:%Y-%m}, "
                f"{float(latest_month['ReturningCustomerPct']):.2f}% "
                "of active customers were returning customers."
            ),
        }
    )

    highest_revenue_channel = (
        channel_summary.sort_values(
            "Revenue",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area": "Preferences",
            "Observation": (
                f"Customers whose preferred channel was "
                f"{highest_revenue_channel['PreferredChannelName']} "
                "generated the largest aggregate lifetime revenue."
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
        "EDA 04: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()