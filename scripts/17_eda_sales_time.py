"""
UAE Retail Intelligence Platform
EDA 02 - Sales & Time Analysis

Analysis:
- Annual performance
- Monthly trends
- Year-over-Year growth
- Day-of-week patterns
- Weekend vs weekday
- UAE retail-event lift
- Rolling averages
- Daily revenue outliers
- Revenue / Orders / AOV relationships
- Monthly seasonality

Outputs:
assets/eda/02_sales_time/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.data_access import (
    get_company_daily_sales,
    get_monthly_company_sales,
    get_sales_detail,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/02_sales_time"
)


EVENT_COLUMNS = {
    "IsRamadan": "Ramadan",
    "IsEidAlFitr": "Eid Al Fitr",
    "IsEidAlAdha": "Eid Al Adha",
    "IsWhiteFriday": "White Friday",
    "IsEidAlEtihad": "Eid Al Etihad",
    "IsSummer": "Summer",
    "IsYearEndSeason": "Year End",
}


DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load_daily_calendar() -> pd.DataFrame:
    """
    Sales detail contains event flags, but has multiple rows per date.
    Aggregate the flags to one Date row and combine them with the
    company-level daily sales series.
    """

    daily = (
        get_company_daily_sales()
    )

    detail = get_sales_detail()

    calendar = (
        detail[
            [
                "FullDate",
                "DayName",
                "IsWeekend",
                *EVENT_COLUMNS.keys(),
            ]
        ]
        .drop_duplicates(
            subset=[
                "FullDate"
            ]
        )
        .copy()
    )

    result = daily.merge(
        calendar,
        on="FullDate",
        how="left",
        validate="one_to_one",
    )

    if result[
        "DayName"
    ].isna().any():
        raise ValueError(
            "Unable to map calendar attributes "
            "to all daily observations."
        )

    return result


def annual_analysis(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    data = daily.copy()

    data[
        "Year"
    ] = (
        data[
            "FullDate"
        ].dt.year
    )

    annual = (
        data.groupby(
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
            NetUnits=(
                "NetUnits",
                "sum",
            ),
        )
    )

    annual[
        "GrossMarginPct"
    ] = (
        annual[
            "GrossProfit"
        ]
        / annual[
            "Revenue"
        ]
        * 100
    )

    annual[
        "YoYGrowthPct"
    ] = (
        annual[
            "Revenue"
        ]
        .pct_change()
        * 100
    )

    return annual


def event_lift_analysis(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for (
        flag_column,
        event_name,
    ) in EVENT_COLUMNS.items():

        event_days = (
            daily.loc[
                daily[
                    flag_column
                ]
                == 1
            ]
        )

        normal_days = (
            daily.loc[
                daily[
                    flag_column
                ]
                == 0
            ]
        )

        if (
            event_days.empty
            or normal_days.empty
        ):
            continue

        event_revenue = float(
            event_days[
                "Revenue"
            ].mean()
        )

        normal_revenue = float(
            normal_days[
                "Revenue"
            ].mean()
        )

        event_orders = float(
            event_days[
                "Orders"
            ].mean()
        )

        normal_orders = float(
            normal_days[
                "Orders"
            ].mean()
        )

        revenue_lift = (
            (
                event_revenue
                - normal_revenue
            )
            / normal_revenue
            * 100
        )

        order_lift = (
            (
                event_orders
                - normal_orders
            )
            / normal_orders
            * 100
        )

        event_aov = (
            event_revenue
            / event_orders
            if event_orders
            else np.nan
        )

        normal_aov = (
            normal_revenue
            / normal_orders
            if normal_orders
            else np.nan
        )

        rows.append(
            {
                "Event": (
                    event_name
                ),
                "EventDays": (
                    len(
                        event_days
                    )
                ),
                "AvgEventRevenue": (
                    event_revenue
                ),
                "AvgNormalRevenue": (
                    normal_revenue
                ),
                "RevenueLiftPct": (
                    revenue_lift
                ),
                "AvgEventOrders": (
                    event_orders
                ),
                "AvgNormalOrders": (
                    normal_orders
                ),
                "OrderLiftPct": (
                    order_lift
                ),
                "EventAOV": (
                    event_aov
                ),
                "NormalAOV": (
                    normal_aov
                ),
            }
        )

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            "RevenueLiftPct",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def detect_daily_outliers(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    IQR-based exploration.

    Outliers are NOT removed. They may represent real retail events.
    """

    q1 = daily[
        "Revenue"
    ].quantile(
        0.25
    )

    q3 = daily[
        "Revenue"
    ].quantile(
        0.75
    )

    iqr = (
        q3 - q1
    )

    lower_bound = (
        q1
        - 1.5 * iqr
    )

    upper_bound = (
        q3
        + 1.5 * iqr
    )

    outliers = (
        daily.loc[
            (
                daily[
                    "Revenue"
                ]
                < lower_bound
            )
            |
            (
                daily[
                    "Revenue"
                ]
                > upper_bound
            )
        ]
        .copy()
    )

    event_flags = list(
        EVENT_COLUMNS.keys()
    )

    outliers[
        "HasRetailEvent"
    ] = (
        outliers[
            event_flags
        ]
        .max(
            axis=1
        )
        .astype(int)
    )

    return (
        outliers.sort_values(
            "Revenue",
            ascending=False,
        )
    )


def main() -> None:
    configure_visuals()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print(
        "EDA 02 - SALES & TIME ANALYSIS"
    )
    print("=" * 78)

    daily = (
        load_daily_calendar()
    )

    monthly = (
        get_monthly_company_sales()
    )

    # ========================================================
    # Feature engineering
    # ========================================================

    daily[
        "Year"
    ] = (
        daily[
            "FullDate"
        ].dt.year
    )

    daily[
        "Month"
    ] = (
        daily[
            "FullDate"
        ].dt.month
    )

    daily[
        "MonthName"
    ] = (
        daily[
            "FullDate"
        ].dt.month_name()
    )

    daily[
        "AOV"
    ] = (
        daily[
            "Revenue"
        ]
        / daily[
            "Orders"
        ].replace(
            0,
            np.nan,
        )
    )

    daily[
        "GrossMarginPct"
    ] = (
        daily[
            "GrossProfit"
        ]
        / daily[
            "Revenue"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    daily[
        "RevenueMA7"
    ] = (
        daily[
            "Revenue"
        ]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    daily[
        "RevenueMA30"
    ] = (
        daily[
            "Revenue"
        ]
        .rolling(
            window=30,
            min_periods=1,
        )
        .mean()
    )

    # ========================================================
    # Annual analysis
    # ========================================================

    annual = (
        annual_analysis(
            daily
        )
    )

    save_csv(
        annual,
        OUTPUT_DIR
        / "annual_performance.csv",
    )

    print(
        "\nAnnual Performance:"
    )

    print(
        annual.round(
            2
        ).to_string(
            index=False
        )
    )

    # ========================================================
    # Annual chart
    # ========================================================

    plt.figure(
        figsize=(
            10,
            6,
        )
    )

    axis = sns.barplot(
        data=annual,
        x="Year",
        y="Revenue",
        color="#2563EB",
    )

    plt.title(
        "Annual Revenue"
    )

    plt.xlabel(
        "Year"
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
        / "annual_revenue.png"
    )

    # ========================================================
    # Monthly trend + rolling averages
    # ========================================================

    plt.figure(
        figsize=(
            16,
            7,
        )
    )

    plt.plot(
        daily[
            "FullDate"
        ],
        daily[
            "Revenue"
        ],
        color="#CBD5E1",
        alpha=0.65,
        linewidth=0.8,
        label="Daily Revenue",
    )

    plt.plot(
        daily[
            "FullDate"
        ],
        daily[
            "RevenueMA7"
        ],
        color="#2563EB",
        linewidth=1.5,
        label="7-Day Moving Average",
    )

    plt.plot(
        daily[
            "FullDate"
        ],
        daily[
            "RevenueMA30"
        ],
        color="#DC2626",
        linewidth=2.0,
        label="30-Day Moving Average",
    )

    plt.title(
        "Daily Revenue and Moving Averages"
    )

    plt.xlabel(
        "Date"
    )

    plt.ylabel(
        "Revenue"
    )

    format_aed_axis(
        plt.gca(),
        "y",
    )

    plt.legend()

    save_figure(
        OUTPUT_DIR
        / "daily_revenue_moving_averages.png"
    )

    # ========================================================
    # Monthly Revenue by Year
    # ========================================================

    monthly_plot = (
        monthly.copy()
    )

    monthly_plot[
        "Year"
    ] = (
        monthly_plot[
            "MonthStart"
        ].dt.year
    )

    monthly_plot[
        "MonthNumber"
    ] = (
        monthly_plot[
            "MonthStart"
        ].dt.month
    )

    plt.figure(
        figsize=(
            14,
            7,
        )
    )

    axis = sns.lineplot(
        data=monthly_plot,
        x="MonthNumber",
        y="Revenue",
        hue="Year",
        marker="o",
        linewidth=2,
        palette="viridis",
    )

    plt.title(
        "Monthly Revenue by Year"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Revenue"
    )

    plt.xticks(
        ticks=range(
            1,
            13,
        )
    )

    format_aed_axis(
        axis,
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "monthly_revenue_yoy.png"
    )

    # ========================================================
    # Day of Week
    # ========================================================

    day_analysis = (
        daily.groupby(
            "DayName",
            as_index=False,
        )
        .agg(
            AvgRevenue=(
                "Revenue",
                "mean",
            ),
            AvgOrders=(
                "Orders",
                "mean",
            ),
            AvgAOV=(
                "AOV",
                "mean",
            ),
        )
    )

    day_analysis[
        "DayName"
    ] = pd.Categorical(
        day_analysis[
            "DayName"
        ],
        categories=DAY_ORDER,
        ordered=True,
    )

    day_analysis = (
        day_analysis.sort_values(
            "DayName"
        )
    )

    save_csv(
        day_analysis,
        OUTPUT_DIR
        / "day_of_week_analysis.csv",
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    axis = sns.barplot(
        data=day_analysis,
        x="DayName",
        y="AvgRevenue",
        color="#0891B2",
    )

    plt.title(
        "Average Daily Revenue by Day of Week"
    )

    plt.xlabel(
        "Day"
    )

    plt.ylabel(
        "Average Revenue"
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
        / "revenue_by_day_of_week.png"
    )

    # ========================================================
    # Weekend Effect
    # ========================================================

    weekend_analysis = (
        daily.assign(
            DayType=np.where(
                daily[
                    "IsWeekend"
                ]
                == 1,
                "Weekend",
                "Weekday",
            )
        )
        .groupby(
            "DayType",
            as_index=False,
        )
        .agg(
            Days=(
                "FullDate",
                "count",
            ),
            AvgRevenue=(
                "Revenue",
                "mean",
            ),
            AvgOrders=(
                "Orders",
                "mean",
            ),
            AvgAOV=(
                "AOV",
                "mean",
            ),
        )
    )

    save_csv(
        weekend_analysis,
        OUTPUT_DIR
        / "weekend_analysis.csv",
    )

    # ========================================================
    # UAE Event Lift
    # ========================================================

    event_lift = (
        event_lift_analysis(
            daily
        )
    )

    save_csv(
        event_lift,
        OUTPUT_DIR
        / "event_lift_analysis.csv",
    )

    print(
        "\nRetail Event Lift:"
    )

    print(
        event_lift[
            [
                "Event",
                "EventDays",
                "RevenueLiftPct",
                "OrderLiftPct",
                "EventAOV",
            ]
        ]
        .round(
            2
        )
        .to_string(
            index=False
        )
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    event_chart = (
        event_lift.sort_values(
            "RevenueLiftPct",
            ascending=True,
        )
    )

    axis = sns.barplot(
        data=event_chart,
        y="Event",
        x="RevenueLiftPct",
        color="#7C3AED",
    )

    plt.axvline(
        0,
        color="black",
        linewidth=1,
    )

    plt.title(
        "Average Daily Revenue Lift During Retail Events"
    )

    plt.xlabel(
        "Revenue Lift (%)"
    )

    plt.ylabel(
        ""
    )

    save_figure(
        OUTPUT_DIR
        / "event_revenue_lift.png"
    )

    # ========================================================
    # Month-of-Year seasonality
    # ========================================================

    seasonality = (
        daily.groupby(
            "Month",
            as_index=False,
        )
        .agg(
            AvgDailyRevenue=(
                "Revenue",
                "mean",
            ),
            AvgDailyOrders=(
                "Orders",
                "mean",
            ),
            AvgAOV=(
                "AOV",
                "mean",
            ),
        )
    )

    save_csv(
        seasonality,
        OUTPUT_DIR
        / "month_of_year_seasonality.csv",
    )

    # ========================================================
    # Revenue / Orders / AOV correlations
    # ========================================================

    correlation_columns = [
        "Revenue",
        "Orders",
        "NetUnits",
        "GrossProfit",
        "DiscountAmount",
        "AOV",
    ]

    correlation = (
        daily[
            correlation_columns
        ]
        .corr(
            method="pearson"
        )
    )

    correlation.to_csv(
        OUTPUT_DIR
        / "sales_correlation_matrix.csv",
        encoding="utf-8-sig",
    )

    plt.figure(
        figsize=(
            9,
            7,
        )
    )

    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
    )

    plt.title(
        "Sales Metric Correlation Matrix"
    )

    save_figure(
        OUTPUT_DIR
        / "sales_correlation_heatmap.png"
    )

    # ========================================================
    # Daily Revenue Outliers
    # ========================================================

    outliers = (
        detect_daily_outliers(
            daily
        )
    )

    save_csv(
        outliers,
        OUTPUT_DIR
        / "daily_revenue_outliers.csv",
    )

    plt.figure(
        figsize=(
            16,
            7,
        )
    )

    plt.scatter(
        daily[
            "FullDate"
        ],
        daily[
            "Revenue"
        ],
        s=12,
        alpha=0.5,
        color="#64748B",
        label="Normal Observation",
    )

    if not outliers.empty:
        plt.scatter(
            outliers[
                "FullDate"
            ],
            outliers[
                "Revenue"
            ],
            s=40,
            color="#DC2626",
            label="IQR Outlier",
        )

    plt.title(
        "Daily Revenue Outlier Exploration"
    )

    plt.xlabel(
        "Date"
    )

    plt.ylabel(
        "Revenue"
    )

    format_aed_axis(
        plt.gca(),
        "y",
    )

    plt.legend()

    save_figure(
        OUTPUT_DIR
        / "daily_revenue_outliers.png"
    )

    # ========================================================
    # Business observations
    # ========================================================

    observations = []

    annual_valid = (
        annual.dropna(
            subset=[
                "YoYGrowthPct"
            ]
        )
    )

    for row in (
        annual_valid.itertuples(
            index=False
        )
    ):
        observations.append(
            {
                "Area":
                    "Growth",

                "Observation":
                    (
                        f"Revenue growth in "
                        f"{row.Year} was "
                        f"{float(row.YoYGrowthPct):.2f}% "
                        f"versus the previous year."
                    ),
            }
        )

    strongest_event = (
        event_lift.iloc[0]
    )

    observations.append(
        {
            "Area":
                "Seasonality",

            "Observation":
                (
                    f"{strongest_event['Event']} "
                    "had the strongest observed "
                    "average daily revenue lift at "
                    f"{float(strongest_event['RevenueLiftPct']):.2f}%."
                ),
        }
    )

    weakest_event = (
        event_lift.iloc[-1]
    )

    observations.append(
        {
            "Area":
                "Seasonality",

            "Observation":
                (
                    f"{weakest_event['Event']} "
                    "had the lowest measured event "
                    "revenue lift at "
                    f"{float(weakest_event['RevenueLiftPct']):.2f}%."
                ),
        }
    )

    best_day = (
        day_analysis.sort_values(
            "AvgRevenue",
            ascending=False,
        ).iloc[0]
    )

    observations.append(
        {
            "Area":
                "Day of Week",

            "Observation":
                (
                    f"{best_day['DayName']} "
                    "had the highest average "
                    "daily revenue."
                ),
        }
    )

    event_outlier_share = (
        (
            outliers[
                "HasRetailEvent"
            ].mean()
            * 100
        )
        if not outliers.empty
        else 0
    )

    observations.append(
        {
            "Area":
                "Outliers",

            "Observation":
                (
                    f"{event_outlier_share:.2f}% "
                    "of IQR revenue outliers "
                    "occurred on dates carrying "
                    "at least one modeled retail "
                    "event flag."
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
        "EDA 02: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()