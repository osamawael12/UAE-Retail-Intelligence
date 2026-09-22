"""
UAE Retail Intelligence Platform
EDA 01 - Data Overview

Purpose:
- Understand analytical dataset sizes.
- Inspect data types and missing values.
- Validate date coverage.
- Review numerical distributions.
- Reconcile executive KPIs.
- Produce reusable EDA artifacts.

Outputs:
assets/eda/01_overview/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analytics.data_access import (
    get_company_daily_sales,
    get_customer_360,
    get_executive_summary,
    get_inventory_status,
    get_monthly_company_sales,
    get_product_performance,
    get_returns,
    get_store_performance,
    get_target_performance,
)
from src.analytics.eda import (
    configure_visuals,
    dataframe_profile,
    format_aed_axis,
    missing_value_report,
    numeric_summary,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/01_overview"
)


def main() -> None:
    configure_visuals()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print(
        "EDA 01 - DATA OVERVIEW"
    )
    print("=" * 78)

    datasets = {
        "daily_sales":
            get_company_daily_sales(),

        "monthly_sales":
            get_monthly_company_sales(),

        "stores":
            get_store_performance(),

        "products":
            get_product_performance(),

        "customers":
            get_customer_360(),

        "returns":
            get_returns(),

        "inventory":
            get_inventory_status(),

        "targets":
            get_target_performance(),
    }

    # ========================================================
    # Dataset profiles
    # ========================================================

    profile_rows = []

    for (
        name,
        dataframe,
    ) in datasets.items():
        profile = (
            dataframe_profile(
                dataframe
            )
        )

        profile_rows.append(
            {
                "Dataset": name,
                **profile,
            }
        )

    profiles = pd.DataFrame(
        profile_rows
    )

    save_csv(
        profiles,
        OUTPUT_DIR
        / "dataset_profiles.csv",
    )

    print(
        "\nDataset Profiles:"
    )

    print(
        profiles.to_string(
            index=False
        )
    )

    # ========================================================
    # Missing values
    # ========================================================

    missing_reports = []

    for (
        name,
        dataframe,
    ) in datasets.items():
        report = (
            missing_value_report(
                dataframe
            )
        )

        if not report.empty:
            report.insert(
                0,
                "Dataset",
                name,
            )

            missing_reports.append(
                report
            )

    if missing_reports:
        missing = pd.concat(
            missing_reports,
            ignore_index=True,
        )
    else:
        missing = pd.DataFrame(
            columns=[
                "Dataset",
                "Column",
                "MissingCount",
                "MissingPct",
            ]
        )

    save_csv(
        missing,
        OUTPUT_DIR
        / "missing_values.csv",
    )

    # ========================================================
    # Numeric summaries
    # ========================================================

    for name in [
        "daily_sales",
        "monthly_sales",
        "stores",
        "products",
        "customers",
        "inventory",
    ]:
        summary = (
            numeric_summary(
                datasets[name]
            )
        )

        if summary.empty:
            continue

        summary = (
            summary
            .reset_index()
            .rename(
                columns={
                    "index":
                        "Variable"
                }
            )
        )

        save_csv(
            summary,
            OUTPUT_DIR
            / (
                f"{name}_"
                "numeric_summary.csv"
            ),
        )

    # ========================================================
    # Date coverage
    # ========================================================

    daily = datasets[
        "daily_sales"
    ]

    date_summary = pd.DataFrame(
        [
            {
                "StartDate":
                    daily[
                        "FullDate"
                    ].min(),

                "EndDate":
                    daily[
                        "FullDate"
                    ].max(),

                "Observations":
                    len(daily),

                "MissingDates":
                    (
                        pd.date_range(
                            daily[
                                "FullDate"
                            ].min(),
                            daily[
                                "FullDate"
                            ].max(),
                            freq="D",
                        )
                        .difference(
                            daily[
                                "FullDate"
                            ]
                        )
                        .size
                    ),
            }
        ]
    )

    save_csv(
        date_summary,
        OUTPUT_DIR
        / "date_coverage.csv",
    )

    # ========================================================
    # Executive KPIs
    # ========================================================

    kpis = (
        get_executive_summary()
    )

    kpi_table = pd.DataFrame(
        [
            {
                "Metric": "Revenue",
                "Value": (
                    float(
                        kpis[
                            "Revenue"
                        ]
                    )
                ),
            },
            {
                "Metric":
                    "Gross Profit",
                "Value": (
                    float(
                        kpis[
                            "GrossProfit"
                        ]
                    )
                ),
            },
            {
                "Metric":
                    "Gross Margin %",
                "Value": (
                    float(
                        kpis[
                            "GrossMarginPct"
                        ]
                    )
                ),
            },
            {
                "Metric": "Orders",
                "Value": (
                    int(
                        kpis[
                            "Orders"
                        ]
                    )
                ),
            },
            {
                "Metric":
                    "Customers",
                "Value": (
                    int(
                        kpis[
                            "Customers"
                        ]
                    )
                ),
            },
            {
                "Metric": "AOV",
                "Value": (
                    float(
                        kpis[
                            "AOV"
                        ]
                    )
                ),
            },
            {
                "Metric":
                    "Return Rate %",
                "Value": (
                    float(
                        kpis[
                            "ReturnRatePct"
                        ]
                    )
                ),
            },
        ]
    )

    save_csv(
        kpi_table,
        OUTPUT_DIR
        / "executive_kpis.csv",
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
        data=daily,
        x="Revenue",
        bins=40,
        kde=True,
        color="#2563EB",
    )

    plt.title(
        "Distribution of Daily Revenue"
    )

    plt.xlabel(
        "Daily Revenue"
    )

    plt.ylabel(
        "Number of Days"
    )

    format_aed_axis(
        plt.gca(),
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "daily_revenue_distribution.png"
    )

    # ========================================================
    # Monthly revenue trend
    # ========================================================

    monthly = datasets[
        "monthly_sales"
    ]

    plt.figure(
        figsize=(
            14,
            6,
        )
    )

    sns.lineplot(
        data=monthly,
        x="MonthStart",
        y="Revenue",
        marker="o",
        linewidth=2,
        color="#0F766E",
    )

    plt.title(
        "Monthly Revenue 2023-2025"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Revenue"
    )

    format_aed_axis(
        plt.gca(),
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "monthly_revenue_trend.png"
    )

    # ========================================================
    # Store revenue distribution
    # ========================================================

    stores = datasets[
        "stores"
    ]

    stores_sorted = (
        stores.sort_values(
            "Revenue",
            ascending=False,
        )
    )

    plt.figure(
        figsize=(
            14,
            8,
        )
    )

    sns.barplot(
        data=stores_sorted,
        y="StoreCode",
        x="Revenue",
        hue="EmirateName",
        dodge=False,
    )

    plt.title(
        "Revenue by Store"
    )

    plt.xlabel(
        "Revenue"
    )

    plt.ylabel(
        "Store"
    )

    format_aed_axis(
        plt.gca(),
        "x",
    )

    plt.legend(
        title="Emirate",
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    save_figure(
        OUTPUT_DIR
        / "store_revenue.png"
    )

    # ========================================================
    # Product revenue distribution
    # ========================================================

    products = datasets[
        "products"
    ]

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=products,
        x="Revenue",
        bins=50,
        kde=True,
        color="#7C3AED",
    )

    plt.title(
        "Product Revenue Distribution"
    )

    plt.xlabel(
        "Product Revenue"
    )

    plt.ylabel(
        "Number of Products"
    )

    format_aed_axis(
        plt.gca(),
        "x",
    )

    save_figure(
        OUTPUT_DIR
        / "product_revenue_distribution.png"
    )

    # ========================================================
    # Customer revenue distribution
    # ========================================================

    customers = datasets[
        "customers"
    ]

    purchasing_customers = (
        customers.loc[
            customers[
                "Orders"
            ]
            > 0
        ]
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=purchasing_customers,
        x="Revenue",
        bins=50,
        kde=True,
        color="#EA580C",
    )

    plt.title(
        "Customer Revenue Distribution"
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
    # Initial observations
    # ========================================================

    observations = []

    annual = (
        monthly.assign(
            Year=(
                monthly[
                    "MonthStart"
                ].dt.year
            )
        )
        .groupby(
            "Year",
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
            Orders=(
                "Orders",
                "sum",
            ),
        )
    )

    for row in (
        annual.itertuples(
            index=False
        )
    ):
        observations.append(
            {
                "Area":
                    "Annual Performance",

                "Observation":
                    (
                        f"{row.Year} revenue = "
                        f"AED "
                        f"{float(row.Revenue):,.2f}"
                    ),
            }
        )

    best_store = (
        stores.sort_values(
            "Revenue",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area":
                "Store Performance",

            "Observation":
                (
                    f"Highest revenue store: "
                    f"{best_store['StoreName']} "
                    f"with AED "
                    f"{float(best_store['Revenue']):,.2f}"
                ),
        }
    )

    highest_return_product = (
        products.sort_values(
            "ReturnRatePct",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area":
                "Product Returns",

            "Observation":
                (
                    "Highest lifetime product "
                    "return rate: "
                    f"{highest_return_product['SKU']} "
                    f"at "
                    f"{float(highest_return_product['ReturnRatePct']):.2f}%"
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
        / "initial_observations.csv",
    )

    print(
        "\nExecutive KPIs:"
    )

    print(
        kpi_table.to_string(
            index=False
        )
    )

    print(
        "\nInitial Observations:"
    )

    print(
        observations_df.to_string(
            index=False
        )
    )

    print()
    print("-" * 78)

    print(
        "EDA 01: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()