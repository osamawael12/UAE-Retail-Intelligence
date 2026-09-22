"""
UAE Retail Intelligence Platform
EDA 06 - Returns & Inventory Analysis

Analysis:
- Return KPI summary
- Return reasons
- Return lag
- Return rates by category
- Return rates by store
- Product return anomaly detection
- Quarterly return anomalies
- Ground-truth anomaly comparison
- Inventory status
- Inventory value
- Reorder risk
- Slow / fast movers
- Inventory risk candidates

Outputs:
assets/eda/06_returns_inventory/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from config.generation_config import (
    CONFIG,
)
from src.analytics.data_access import (
    get_inventory_status,
    get_product_performance,
    get_returns,
    get_sales_detail,
)
from src.analytics.eda import (
    configure_visuals,
    format_aed_axis,
    save_csv,
    save_figure,
)


OUTPUT_DIR = Path(
    "assets/eda/06_returns_inventory"
)


MIN_PRODUCT_UNITS = 50

MIN_QUARTER_UNITS = 20


def build_return_kpis(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    gross_units = float(
        sales[
            "GrossUnits"
        ].sum()
    )

    returned_units = float(
        sales[
            "ReturnedUnits"
        ].sum()
    )

    net_sales_before_returns = float(
        sales[
            "NetSalesBeforeReturns"
        ].sum()
    )

    returned_net_sales = float(
        sales[
            "ReturnedNetSales"
        ].sum()
    )

    refund_amount = float(
        returns[
            "RefundAmount"
        ].sum()
    )

    average_return_lag = float(
        returns[
            "ReturnLagDays"
        ].mean()
    )

    return pd.DataFrame(
        [
            {
                "Metric":
                    "Gross Units Sold",
                "Value":
                    gross_units,
            },
            {
                "Metric":
                    "Returned Units",
                "Value":
                    returned_units,
            },
            {
                "Metric":
                    "Unit Return Rate %",
                "Value":
                    (
                        returned_units
                        / gross_units
                        * 100
                        if gross_units
                        else 0
                    ),
            },
            {
                "Metric":
                    "Returned Net Sales",
                "Value":
                    returned_net_sales,
            },
            {
                "Metric":
                    "Value Return Rate %",
                "Value":
                    (
                        returned_net_sales
                        / net_sales_before_returns
                        * 100
                        if net_sales_before_returns
                        else 0
                    ),
            },
            {
                "Metric":
                    "Refund Amount",
                "Value":
                    refund_amount,
            },
            {
                "Metric":
                    "Average Return Lag Days",
                "Value":
                    average_return_lag,
            },
        ]
    )


def build_category_returns(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales.groupby(
            "CategoryName",
            as_index=False,
        )
        .agg(
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
            NetSalesBeforeReturns=(
                "NetSalesBeforeReturns",
                "sum",
            ),
            ReturnedNetSales=(
                "ReturnedNetSales",
                "sum",
            ),
        )
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
        "ValueReturnRatePct"
    ] = (
        summary[
            "ReturnedNetSales"
        ]
        / summary[
            "NetSalesBeforeReturns"
        ].replace(
            0,
            np.nan,
        )
        * 100
    )

    return (
        summary.sort_values(
            "ReturnRatePct",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def build_store_returns(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    summary = (
        sales.groupby(
            [
                "StoreId",
                "StoreCode",
                "StoreName",
                "EmirateName",
            ],
            as_index=False,
        )
        .agg(
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
        )
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
            "ReturnRatePct",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


def build_product_anomalies(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    product = (
        sales.groupby(
            [
                "ProductId",
                "SKU",
                "ProductName",
                "CategoryName",
            ],
            as_index=False,
        )
        .agg(
            GrossUnits=(
                "GrossUnits",
                "sum",
            ),
            ReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
            Revenue=(
                "Revenue",
                "sum",
            ),
        )
    )

    product[
        "ProductReturnRate"
    ] = (
        product[
            "ReturnedUnits"
        ]
        / product[
            "GrossUnits"
        ].replace(
            0,
            np.nan,
        )
    )

    category = (
        product.groupby(
            "CategoryName",
            as_index=False,
        )
        .agg(
            CategoryGrossUnits=(
                "GrossUnits",
                "sum",
            ),
            CategoryReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
        )
    )

    category[
        "CategoryReturnRate"
    ] = (
        category[
            "CategoryReturnedUnits"
        ]
        / category[
            "CategoryGrossUnits"
        ].replace(
            0,
            np.nan,
        )
    )

    result = (
        product.merge(
            category[
                [
                    "CategoryName",
                    "CategoryReturnRate",
                ]
            ],
            on="CategoryName",
            how="left",
            validate="many_to_one",
        )
    )

    result[
        "ProductReturnRatePct"
    ] = (
        result[
            "ProductReturnRate"
        ]
        * 100
    )

    result[
        "CategoryReturnRatePct"
    ] = (
        result[
            "CategoryReturnRate"
        ]
        * 100
    )

    result[
        "ExcessReturnPctPoints"
    ] = (
        result[
            "ProductReturnRatePct"
        ]
        - result[
            "CategoryReturnRatePct"
        ]
    )

    result[
        "CategoryRateMultiplier"
    ] = (
        result[
            "ProductReturnRate"
        ]
        / result[
            "CategoryReturnRate"
        ].replace(
            0,
            np.nan,
        )
    )

    eligible = (
        result.loc[
            result[
                "GrossUnits"
            ]
            >= MIN_PRODUCT_UNITS
        ]
        .copy()
    )

    multiplier_q95 = float(
        eligible[
            "CategoryRateMultiplier"
        ].quantile(
            0.95
        )
    )

    eligible[
        "IsAnomalyCandidate"
    ] = (
        eligible[
            "CategoryRateMultiplier"
        ]
        >= multiplier_q95
    )

    eligible[
        "AnomalyThreshold"
    ] = (
        multiplier_q95
    )

    return (
        eligible.sort_values(
            [
                "CategoryRateMultiplier",
                "ReturnedUnits",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )


def build_quarterly_anomalies(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    data = (
        sales.copy()
    )

    data[
        "Year"
    ] = (
        data[
            "FullDate"
        ].dt.year
    )

    data[
        "Quarter"
    ] = (
        data[
            "FullDate"
        ].dt.quarter
    )

    product_quarter = (
        data.groupby(
            [
                "Year",
                "Quarter",
                "ProductId",
                "SKU",
                "ProductName",
                "CategoryName",
            ],
            as_index=False,
        )
        .agg(
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

    category_quarter = (
        product_quarter.groupby(
            [
                "Year",
                "Quarter",
                "CategoryName",
            ],
            as_index=False,
        )
        .agg(
            CategoryGrossUnits=(
                "GrossUnits",
                "sum",
            ),
            CategoryReturnedUnits=(
                "ReturnedUnits",
                "sum",
            ),
        )
    )

    category_quarter[
        "CategoryReturnRate"
    ] = (
        category_quarter[
            "CategoryReturnedUnits"
        ]
        / category_quarter[
            "CategoryGrossUnits"
        ].replace(
            0,
            np.nan,
        )
    )

    result = (
        product_quarter.merge(
            category_quarter[
                [
                    "Year",
                    "Quarter",
                    "CategoryName",
                    "CategoryReturnRate",
                ]
            ],
            on=[
                "Year",
                "Quarter",
                "CategoryName",
            ],
            how="left",
            validate="many_to_one",
        )
    )

    result[
        "ProductReturnRate"
    ] = (
        result[
            "ReturnedUnits"
        ]
        / result[
            "GrossUnits"
        ].replace(
            0,
            np.nan,
        )
    )

    result[
        "ProductReturnRatePct"
    ] = (
        result[
            "ProductReturnRate"
        ]
        * 100
    )

    result[
        "CategoryReturnRatePct"
    ] = (
        result[
            "CategoryReturnRate"
        ]
        * 100
    )

    result[
        "CategoryRateMultiplier"
    ] = (
        result[
            "ProductReturnRate"
        ]
        / result[
            "CategoryReturnRate"
        ].replace(
            0,
            np.nan,
        )
    )

    eligible = (
        result.loc[
            result[
                "GrossUnits"
            ]
            >= MIN_QUARTER_UNITS
        ]
        .copy()
    )

    eligible[
        "QuarterLabel"
    ] = (
        eligible[
            "Year"
        ].astype(str)
        + " Q"
        + eligible[
            "Quarter"
        ].astype(str)
    )

    threshold = float(
        eligible[
            "CategoryRateMultiplier"
        ].quantile(
            0.97
        )
    )

    eligible[
        "IsAnomalyCandidate"
    ] = (
        eligible[
            "CategoryRateMultiplier"
        ]
        >= threshold
    )

    return (
        eligible.sort_values(
            [
                "CategoryRateMultiplier",
                "ReturnedUnits",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )


def compare_with_ground_truth(
    detected: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ground truth is only used AFTER anomaly detection.
    """

    manifest_path = (
        CONFIG.output_directory
        / "simulation_return_anomaly_manifest.csv"
    )

    if not manifest_path.exists():
        return pd.DataFrame()

    manifest = pd.read_csv(
        manifest_path
    )

    manifest[
        "StartDate"
    ] = pd.to_datetime(
        manifest[
            "StartDate"
        ]
    )

    manifest[
        "EndDate"
    ] = pd.to_datetime(
        manifest[
            "EndDate"
        ]
    )

    truth_ids = set(
        manifest[
            "ProductId"
        ].astype(int)
    )

    candidate_rows = (
        detected.loc[
            detected[
                "IsAnomalyCandidate"
            ]
        ]
    )

    detected_ids = set(
        candidate_rows[
            "ProductId"
        ].astype(int)
    )

    rows = []

    for product_id in sorted(
        truth_ids
        | detected_ids
    ):
        rows.append(
            {
                "ProductId":
                    product_id,

                "InjectedAnomaly":
                    int(
                        product_id
                        in truth_ids
                    ),

                "DetectedCandidate":
                    int(
                        product_id
                        in detected_ids
                    ),
            }
        )

    result = pd.DataFrame(
        rows
    )

    if not result.empty:
        result[
            "CorrectDetection"
        ] = (
            (
                result[
                    "InjectedAnomaly"
                ]
                == 1
            )
            & (
                result[
                    "DetectedCandidate"
                ]
                == 1
            )
        ).astype(int)

    return result


def main() -> None:
    configure_visuals()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print(
        "EDA 06 - RETURNS & INVENTORY"
    )
    print("=" * 78)

    sales = (
        get_sales_detail()
    )

    returns = (
        get_returns()
    )

    inventory = (
        get_inventory_status()
    )

    products = (
        get_product_performance()
    )

    # ========================================================
    # Return KPIs
    # ========================================================

    return_kpis = (
        build_return_kpis(
            sales,
            returns,
        )
    )

    save_csv(
        return_kpis,
        OUTPUT_DIR
        / "return_kpis.csv",
    )

    print(
        "\nReturn KPIs:"
    )

    print(
        return_kpis.round(
            2
        ).to_string(
            index=False
        )
    )

    # ========================================================
    # Return reasons
    # ========================================================

    reason_summary = (
        returns.groupby(
            "ReturnReason",
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
            ReturnedNetSales=(
                "ReturnedNetAmount",
                "sum",
            ),
            RefundAmount=(
                "RefundAmount",
                "sum",
            ),
        )
        .sort_values(
            "ReturnedUnits",
            ascending=False,
        )
    )

    save_csv(
        reason_summary,
        OUTPUT_DIR
        / "return_reason_summary.csv",
    )

    plt.figure(
        figsize=(
            12,
            7,
        )
    )

    sns.barplot(
        data=reason_summary,
        y="ReturnReason",
        x="ReturnedUnits",
        color="#DC2626",
    )

    plt.title(
        "Returned Units by Return Reason"
    )

    plt.xlabel(
        "Returned Units"
    )

    plt.ylabel(
        ""
    )

    save_figure(
        OUTPUT_DIR
        / "return_reasons.png"
    )

    # ========================================================
    # Return lag
    # ========================================================

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.histplot(
        data=returns,
        x="ReturnLagDays",
        bins=30,
        kde=True,
        color="#EA580C",
    )

    plt.title(
        "Return Lag Distribution"
    )

    plt.xlabel(
        "Days Between Sale and Return"
    )

    plt.ylabel(
        "Return Lines"
    )

    save_figure(
        OUTPUT_DIR
        / "return_lag_distribution.png"
    )

    # ========================================================
    # Category returns
    # ========================================================

    category_returns = (
        build_category_returns(
            sales
        )
    )

    save_csv(
        category_returns,
        OUTPUT_DIR
        / "category_return_rates.csv",
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    sns.barplot(
        data=category_returns,
        y="CategoryName",
        x="ReturnRatePct",
        color="#7C3AED",
    )

    plt.title(
        "Unit Return Rate by Category"
    )

    plt.xlabel(
        "Return Rate (%)"
    )

    plt.ylabel(
        ""
    )

    save_figure(
        OUTPUT_DIR
        / "category_return_rates.png"
    )

    # ========================================================
    # Store returns
    # ========================================================

    store_returns = (
        build_store_returns(
            sales
        )
    )

    save_csv(
        store_returns,
        OUTPUT_DIR
        / "store_return_rates.csv",
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sns.barplot(
        data=store_returns,
        y="StoreCode",
        x="ReturnRatePct",
        hue="EmirateName",
        dodge=False,
    )

    plt.title(
        "Return Rate by Store"
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
        / "store_return_rates.png"
    )

    # ========================================================
    # Lifetime product anomalies
    # ========================================================

    product_anomalies = (
        build_product_anomalies(
            sales
        )
    )

    save_csv(
        product_anomalies,
        OUTPUT_DIR
        / "product_return_anomalies.csv",
    )

    top_product_anomalies = (
        product_anomalies.head(
            25
        )
    )

    plt.figure(
        figsize=(
            13,
            9,
        )
    )

    sns.barplot(
        data=top_product_anomalies,
        y="SKU",
        x="CategoryRateMultiplier",
        hue="CategoryName",
        dodge=False,
    )

    plt.axvline(
        1,
        color="black",
        linestyle="--",
    )

    plt.title(
        "Products with Elevated Return Rates vs Category"
    )

    plt.xlabel(
        "Product Return Rate / Category Return Rate"
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
        / "product_return_anomalies.png"
    )

    # ========================================================
    # Quarterly anomalies
    # ========================================================

    quarterly = (
        build_quarterly_anomalies(
            sales
        )
    )

    save_csv(
        quarterly,
        OUTPUT_DIR
        / "quarterly_product_return_anomalies.csv",
    )

    quarterly_candidates = (
        quarterly.loc[
            quarterly[
                "IsAnomalyCandidate"
            ]
        ]
        .copy()
    )

    save_csv(
        quarterly_candidates,
        OUTPUT_DIR
        / "detected_quarterly_anomaly_candidates.csv",
    )

    top_quarterly = (
        quarterly.head(
            35
        )
    )

    plt.figure(
        figsize=(
            14,
            10,
        )
    )

    sns.scatterplot(
        data=top_quarterly,
        x="CategoryRateMultiplier",
        y="ReturnedUnits",
        hue="QuarterLabel",
        size="GrossUnits",
        sizes=(
            40,
            300,
        ),
        alpha=0.8,
    )

    plt.axvline(
        1,
        color="black",
        linestyle="--",
    )

    plt.title(
        "Quarterly Product Return Anomaly Candidates"
    )

    plt.xlabel(
        "Product Return Rate / Category Return Rate"
    )

    plt.ylabel(
        "Returned Units"
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
        / "quarterly_return_anomalies.png"
    )

    # ========================================================
    # Ground truth comparison
    # ========================================================

    anomaly_validation = (
        compare_with_ground_truth(
            quarterly
        )
    )

    if not anomaly_validation.empty:
        save_csv(
            anomaly_validation,
            OUTPUT_DIR
            / "anomaly_ground_truth_comparison.csv",
        )

    # ========================================================
    # Inventory KPIs
    # ========================================================

    inventory[
        "InventoryValue"
    ] = pd.to_numeric(
        inventory[
            "InventoryValue"
        ]
    )

    inventory_summary = pd.DataFrame(
        [
            {
                "Metric":
                    "Store/Product Records",
                "Value":
                    len(inventory),
            },
            {
                "Metric":
                    "Stock On Hand Units",
                "Value":
                    inventory[
                        "CurrentStock"
                    ].sum(),
            },
            {
                "Metric":
                    "Inventory Value",
                "Value":
                    inventory[
                        "InventoryValue"
                    ].sum(),
            },
            {
                "Metric":
                    "Stockouts",
                "Value":
                    (
                        inventory[
                            "StockStatus"
                        ]
                        == "STOCKOUT"
                    ).sum(),
            },
            {
                "Metric":
                    "Low Stock",
                "Value":
                    (
                        inventory[
                            "StockStatus"
                        ]
                        == "LOW_STOCK"
                    ).sum(),
            },
        ]
    )

    save_csv(
        inventory_summary,
        OUTPUT_DIR
        / "inventory_kpis.csv",
    )

    # ========================================================
    # Stock Status
    # ========================================================

    stock_status = (
        inventory[
            "StockStatus"
        ]
        .value_counts()
        .rename_axis(
            "StockStatus"
        )
        .reset_index(
            name="SKUs"
        )
    )

    stock_status[
        "Pct"
    ] = (
        stock_status[
            "SKUs"
        ]
        / len(inventory)
        * 100
    )

    save_csv(
        stock_status,
        OUTPUT_DIR
        / "stock_status_summary.csv",
    )

    plt.figure(
        figsize=(
            9,
            6,
        )
    )

    sns.barplot(
        data=stock_status,
        x="StockStatus",
        y="SKUs",
        color="#0F766E",
    )

    plt.title(
        "Current Inventory Status"
    )

    plt.xlabel(
        ""
    )

    plt.ylabel(
        "Store / Product Combinations"
    )

    save_figure(
        OUTPUT_DIR
        / "inventory_status.png"
    )

    # ========================================================
    # Inventory value by category
    # ========================================================

    category_inventory = (
        inventory.groupby(
            "CategoryName",
            as_index=False,
        )
        .agg(
            StockUnits=(
                "CurrentStock",
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
        )
        .sort_values(
            "InventoryValue",
            ascending=False,
        )
    )

    save_csv(
        category_inventory,
        OUTPUT_DIR
        / "inventory_value_by_category.csv",
    )

    plt.figure(
        figsize=(
            12,
            6,
        )
    )

    axis = sns.barplot(
        data=category_inventory,
        y="CategoryName",
        x="InventoryValue",
        color="#2563EB",
    )

    plt.title(
        "Current Inventory Value by Category"
    )

    plt.xlabel(
        "Inventory Value"
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
        / "inventory_value_by_category.png"
    )

    # ========================================================
    # Reorder risk
    # ========================================================

    reorder_summary = (
        inventory[
            "ReorderRisk"
        ]
        .value_counts()
        .rename_axis(
            "ReorderRisk"
        )
        .reset_index(
            name="SKUs"
        )
    )

    save_csv(
        reorder_summary,
        OUTPUT_DIR
        / "reorder_risk_summary.csv",
    )

    reorder_candidates = (
        inventory.loc[
            inventory[
                "ReorderRisk"
            ].isin(
                [
                    "CRITICAL",
                    "HIGH",
                    "MEDIUM",
                ]
            )
        ]
        .sort_values(
            [
                "ReorderRisk",
                "GrossUnitsSold",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    save_csv(
        reorder_candidates,
        OUTPUT_DIR
        / "reorder_candidates.csv",
    )

    # ========================================================
    # Slow movers
    # ========================================================

    product_inventory = (
        inventory.groupby(
            [
                "ProductId",
                "SKU",
                "ProductName",
                "CategoryName",
            ],
            as_index=False,
        )
        .agg(
            StockUnits=(
                "CurrentStock",
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
        )
    )

    product_inventory[
        "SalesVelocityProxy"
    ] = (
        product_inventory[
            "GrossUnitsSold"
        ]
        / 1096
    )

    velocity_q25 = float(
        product_inventory[
            "SalesVelocityProxy"
        ].quantile(
            0.25
        )
    )

    velocity_q75 = float(
        product_inventory[
            "SalesVelocityProxy"
        ].quantile(
            0.75
        )
    )

    product_inventory[
        "MovementClass"
    ] = np.select(
        [
            product_inventory[
                "SalesVelocityProxy"
            ]
            <= velocity_q25,

            product_inventory[
                "SalesVelocityProxy"
            ]
            >= velocity_q75,
        ],
        [
            "SLOW_MOVING",
            "FAST_MOVING",
        ],
        default="NORMAL",
    )

    save_csv(
        product_inventory,
        OUTPUT_DIR
        / "product_inventory_velocity.csv",
    )

    slow_movers = (
        product_inventory.loc[
            product_inventory[
                "MovementClass"
            ]
            == "SLOW_MOVING"
        ]
        .sort_values(
            "InventoryValue",
            ascending=False,
        )
    )

    save_csv(
        slow_movers,
        OUTPUT_DIR
        / "slow_movers.csv",
    )

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    top_slow = (
        slow_movers.head(
            25
        )
    )

    axis = sns.barplot(
        data=top_slow,
        y="SKU",
        x="InventoryValue",
        hue="CategoryName",
        dodge=False,
    )

    plt.title(
        "Slow-Moving Products with Highest Inventory Value"
    )

    plt.xlabel(
        "Inventory Value"
    )

    plt.ylabel(
        "Product"
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
        / "slow_moving_inventory_value.png"
    )

    # ========================================================
    # Inventory Risk Matrix
    # ========================================================

    plt.figure(
        figsize=(
            13,
            8,
        )
    )

    sample_inventory = (
        product_inventory.sample(
            n=min(
                800,
                len(
                    product_inventory
                ),
            ),
            random_state=42,
        )
    )

    sns.scatterplot(
        data=sample_inventory,
        x="SalesVelocityProxy",
        y="InventoryValue",
        hue="MovementClass",
        size="StockUnits",
        sizes=(
            20,
            250,
        ),
        alpha=0.6,
    )

    plt.title(
        "Inventory Value vs Sales Velocity"
    )

    plt.xlabel(
        "Average Units Sold per Day"
    )

    plt.ylabel(
        "Current Inventory Value"
    )

    format_aed_axis(
        plt.gca(),
        "y",
    )

    save_figure(
        OUTPUT_DIR
        / "inventory_velocity_value_matrix.png"
    )

    # ========================================================
    # Business observations
    # ========================================================

    observations = []

    highest_category = (
        category_returns.iloc[0]
    )

    observations.append(
        {
            "Area":
                "Returns",

            "Observation":
                (
                    f"{highest_category['CategoryName']} "
                    "had the highest category unit return "
                    f"rate at "
                    f"{float(highest_category['ReturnRatePct']):.2f}%."
                ),
        }
    )

    top_reason = (
        reason_summary.iloc[0]
    )

    observations.append(
        {
            "Area":
                "Returns",

            "Observation":
                (
                    f"{top_reason['ReturnReason']} "
                    "was the most common return reason "
                    f"with {int(top_reason['ReturnedUnits']):,} "
                    "returned units."
                ),
        }
    )

    candidate_count = int(
        quarterly_candidates[
            "ProductId"
        ].nunique()
    )

    observations.append(
        {
            "Area":
                "Anomaly Detection",

            "Observation":
                (
                    f"The quarterly relative-rate method "
                    f"flagged {candidate_count:,} unique "
                    "products for return-rate investigation."
                ),
        }
    )

    if (
        not anomaly_validation.empty
    ):
        true_count = int(
            anomaly_validation[
                "InjectedAnomaly"
            ].sum()
        )

        detected_true = int(
            anomaly_validation[
                "CorrectDetection"
            ].sum()
        )

        observations.append(
            {
                "Area":
                    "Simulation Validation",

                "Observation":
                    (
                        f"The exploratory detector identified "
                        f"{detected_true} of {true_count} "
                        "synthetically injected quality-issue "
                        "products among its anomaly candidates."
                    ),
            }
        )

    inventory_value = float(
        inventory[
            "InventoryValue"
        ].sum()
    )

    observations.append(
        {
            "Area":
                "Inventory",

            "Observation":
                (
                    "Current simulated inventory value was "
                    f"AED {inventory_value:,.2f}."
                ),
        }
    )

    slow_inventory_value = float(
        slow_movers[
            "InventoryValue"
        ].sum()
    )

    observations.append(
        {
            "Area":
                "Inventory",

            "Observation":
                (
                    "Products classified in the bottom "
                    "sales-velocity quartile held "
                    f"AED {slow_inventory_value:,.2f} "
                    "of current inventory value."
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
        "EDA 06: COMPLETED"
    )

    print(
        f"Artifacts saved to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()