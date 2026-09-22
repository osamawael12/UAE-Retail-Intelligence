"""
UAE Retail Intelligence Platform
Synthetic Store Target Generator

Generates monthly targets for:
- Revenue
- Gross Profit
- Orders

Target grain:
Store x Calendar Month

Business logic:
- 2023 establishes a baseline.
- 2024 uses prior-year same-month performance.
- 2025 uses prior-year same-month performance.
- Targets include expected growth and moderate stretch.
- Revenue uses sales net of merchandise returns.
- Gross Profit uses net revenue and reversed COGS.
- VAT is never included in revenue or profit targets.

No SQL Server writes are performed.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


MONEY_QUANTIZER = Decimal(
    "0.0001"
)


YEAR_GROWTH_EXPECTATION = {
    2023: 0.00,
    2024: 0.08,
    2025: 0.09,
}


MONTH_SEASONALITY = {
    1: 0.94,
    2: 0.95,
    3: 1.04,
    4: 1.08,
    5: 0.98,
    6: 1.01,
    7: 0.94,
    8: 0.96,
    9: 0.98,
    10: 1.00,
    11: 1.13,
    12: 1.17,
}


def money(
    value,
) -> Decimal:
    return Decimal(
        str(value)
    ).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def _prepare_actuals(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    returns: pd.DataFrame,
    return_items: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build actual monthly Store KPIs.

    Revenue:
        Sales NetAmount - ReturnedNetAmount

    Gross Profit:
        Revenue - Net COGS

    Returned COGS is derived proportionally from the original
    order line using returned quantity.
    """

    orders = orders.copy()
    order_items = order_items.copy()
    returns = returns.copy()
    return_items = return_items.copy()

    orders[
        "OrderDateTime"
    ] = pd.to_datetime(
        orders["OrderDateTime"]
    )

    completed_orders = (
        orders.loc[
            orders[
                "OrderStatus"
            ]
            == "COMPLETED"
        ]
        .copy()
    )

    completed_orders["Year"] = (
        completed_orders[
            "OrderDateTime"
        ].dt.year
    )

    completed_orders["Month"] = (
        completed_orders[
            "OrderDateTime"
        ].dt.month
    )

    item_data = (
        order_items.merge(
            completed_orders[
                [
                    "OrderId",
                    "StoreId",
                    "Year",
                    "Month",
                ]
            ],
            on="OrderId",
            how="inner",
            validate="many_to_one",
        )
    )

    item_data[
        "NetAmount"
    ] = pd.to_numeric(
        item_data["NetAmount"]
    )

    item_data[
        "LineCOGS"
    ] = pd.to_numeric(
        item_data["LineCOGS"]
    )

    sales_monthly = (
        item_data.groupby(
            [
                "StoreId",
                "Year",
                "Month",
            ],
            as_index=False,
        )
        .agg(
            GrossNetSales=(
                "NetAmount",
                "sum",
            ),
            GrossCOGS=(
                "LineCOGS",
                "sum",
            ),
        )
    )

    order_monthly = (
        completed_orders.groupby(
            [
                "StoreId",
                "Year",
                "Month",
            ],
            as_index=False,
        )
        .agg(
            Orders=(
                "OrderId",
                "nunique",
            )
        )
    )

    if return_items.empty:
        return_monthly = (
            pd.DataFrame(
                columns=[
                    "StoreId",
                    "Year",
                    "Month",
                    "ReturnedNetSales",
                    "ReturnedCOGS",
                ]
            )
        )

    else:
        return_detail = (
            return_items[
                [
                    "ReturnId",
                    "OrderItemId",
                    "ReturnQuantity",
                    "ReturnedNetAmount",
                ]
            ]
            .merge(
                returns[
                    [
                        "ReturnId",
                        "ReturnStatus",
                    ]
                ],
                on="ReturnId",
                how="inner",
                validate="many_to_one",
            )
        )

        return_detail = (
            return_detail.loc[
                return_detail[
                    "ReturnStatus"
                ]
                == "COMPLETED"
            ]
            .copy()
        )

        return_detail = (
            return_detail.merge(
                item_data[
                    [
                        "OrderItemId",
                        "StoreId",
                        "Year",
                        "Month",
                        "Quantity",
                        "LineCOGS",
                    ]
                ],
                on="OrderItemId",
                how="inner",
                validate="many_to_one",
            )
        )

        return_detail[
            "ReturnedNetAmount"
        ] = pd.to_numeric(
            return_detail[
                "ReturnedNetAmount"
            ]
        )

        return_detail[
            "ReturnQuantity"
        ] = pd.to_numeric(
            return_detail[
                "ReturnQuantity"
            ]
        )

        return_detail[
            "Quantity"
        ] = pd.to_numeric(
            return_detail[
                "Quantity"
            ]
        )

        return_detail[
            "LineCOGS"
        ] = pd.to_numeric(
            return_detail[
                "LineCOGS"
            ]
        )

        return_detail[
            "ReturnedCOGS"
        ] = (
            return_detail[
                "LineCOGS"
            ]
            * (
                return_detail[
                    "ReturnQuantity"
                ]
                / return_detail[
                    "Quantity"
                ]
            )
        )

        # Attribution rule:
        # returns reduce the original sale month for target
        # performance calculations. Return-date analytics
        # will remain available separately later.
        return_monthly = (
            return_detail.groupby(
                [
                    "StoreId",
                    "Year",
                    "Month",
                ],
                as_index=False,
            )
            .agg(
                ReturnedNetSales=(
                    "ReturnedNetAmount",
                    "sum",
                ),
                ReturnedCOGS=(
                    "ReturnedCOGS",
                    "sum",
                ),
            )
        )

    actuals = (
        sales_monthly.merge(
            order_monthly,
            on=[
                "StoreId",
                "Year",
                "Month",
            ],
            how="outer",
            validate="one_to_one",
        )
        .merge(
            return_monthly,
            on=[
                "StoreId",
                "Year",
                "Month",
            ],
            how="left",
            validate="one_to_one",
        )
    )

    numeric_columns = [
        "GrossNetSales",
        "GrossCOGS",
        "Orders",
        "ReturnedNetSales",
        "ReturnedCOGS",
    ]

    for column in numeric_columns:
        actuals[column] = (
            pd.to_numeric(
                actuals[column],
                errors="coerce",
            )
            .fillna(0)
        )

    actuals["Revenue"] = (
        actuals["GrossNetSales"]
        - actuals[
            "ReturnedNetSales"
        ]
    )

    actuals["NetCOGS"] = (
        actuals["GrossCOGS"]
        - actuals[
            "ReturnedCOGS"
        ]
    )

    actuals["GrossProfit"] = (
        actuals["Revenue"]
        - actuals["NetCOGS"]
    )

    return actuals[
        [
            "StoreId",
            "Year",
            "Month",
            "Revenue",
            "GrossProfit",
            "Orders",
        ]
    ]


def _complete_month_grid(
    stores: pd.DataFrame,
    actuals: pd.DataFrame,
) -> pd.DataFrame:
    """
    Guarantee one row for every Store x Month.
    """

    months = pd.period_range(
        start=CONFIG.start_date,
        end=CONFIG.end_date,
        freq="M",
    )

    rows = []

    for store_id in (
        stores[
            "StoreId"
        ].astype(int)
    ):
        for period in months:
            rows.append(
                {
                    "StoreId": int(
                        store_id
                    ),
                    "Year": int(
                        period.year
                    ),
                    "Month": int(
                        period.month
                    ),
                }
            )

    grid = pd.DataFrame(
        rows
    )

    grid = grid.merge(
        actuals,
        on=[
            "StoreId",
            "Year",
            "Month",
        ],
        how="left",
        validate="one_to_one",
    )

    for column in [
        "Revenue",
        "GrossProfit",
        "Orders",
    ]:
        grid[column] = (
            pd.to_numeric(
                grid[column],
                errors="coerce",
            )
            .fillna(0)
        )

    return grid


def _build_2023_baselines(
    grid: pd.DataFrame,
    stores: pd.DataFrame,
) -> dict[
    tuple[int, int],
    dict[str, float],
]:
    """
    Build initial target baselines without directly copying each
    store's current-month actual result.

    Store size and network-level 2023 performance establish
    expected monthly performance.
    """

    data_2023 = (
        grid.loc[
            grid["Year"]
            == 2023
        ]
        .copy()
    )

    annual_network = {
        "Revenue": float(
            data_2023[
                "Revenue"
            ].sum()
        ),
        "GrossProfit": float(
            data_2023[
                "GrossProfit"
            ].sum()
        ),
        "Orders": float(
            data_2023[
                "Orders"
            ].sum()
        ),
    }

    store_size_weights = (
        stores[
            [
                "StoreId",
                "FloorAreaSqM",
            ]
        ]
        .copy()
    )

    store_size_weights[
        "SizeWeight"
    ] = np.sqrt(
        pd.to_numeric(
            store_size_weights[
                "FloorAreaSqM"
            ]
        )
    )

    store_size_weights[
        "SizeWeight"
    ] = (
        store_size_weights[
            "SizeWeight"
        ]
        / store_size_weights[
            "SizeWeight"
        ].sum()
    )

    store_weight_lookup = dict(
        zip(
            store_size_weights[
                "StoreId"
            ].astype(int),
            store_size_weights[
                "SizeWeight"
            ].astype(float),
        )
    )

    seasonality_total = sum(
        MONTH_SEASONALITY.values()
    )

    baselines = {}

    for store_id in (
        stores[
            "StoreId"
        ].astype(int)
    ):
        store_weight = (
            store_weight_lookup[
                store_id
            ]
        )

        for month in range(
            1,
            13,
        ):
            month_weight = (
                MONTH_SEASONALITY[
                    month
                ]
                / seasonality_total
            )

            baselines[
                (
                    store_id,
                    month,
                )
            ] = {
                "Revenue": (
                    annual_network[
                        "Revenue"
                    ]
                    * store_weight
                    * month_weight
                ),
                "GrossProfit": (
                    annual_network[
                        "GrossProfit"
                    ]
                    * store_weight
                    * month_weight
                ),
                "Orders": (
                    annual_network[
                        "Orders"
                    ]
                    * store_weight
                    * month_weight
                ),
            }

    return baselines


def generate_targets(
    stores: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    returns: pd.DataFrame,
    return_items: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(
        CONFIG.random_seed + 1000
    )

    actuals = _prepare_actuals(
        orders=orders,
        order_items=order_items,
        returns=returns,
        return_items=return_items,
    )

    grid = _complete_month_grid(
        stores=stores,
        actuals=actuals,
    )

    baseline_2023 = (
        _build_2023_baselines(
            grid=grid,
            stores=stores,
        )
    )

    actual_lookup = {
        (
            int(row.StoreId),
            int(row.Year),
            int(row.Month),
        ): {
            "Revenue": float(
                row.Revenue
            ),
            "GrossProfit": float(
                row.GrossProfit
            ),
            "Orders": float(
                row.Orders
            ),
        }
        for row in (
            grid.itertuples(
                index=False
            )
        )
    }

    rows = []

    target_id = 1

    for store_id in sorted(
        stores[
            "StoreId"
        ].astype(int)
    ):
        # Persistent management ambition varies by store.
        store_stretch = float(
            rng.uniform(
                0.98,
                1.07,
            )
        )

        for year in range(
            CONFIG.start_date.year,
            CONFIG.end_date.year + 1,
        ):
            for month in range(
                1,
                13,
            ):
                if year == 2023:
                    source = (
                        baseline_2023[
                            (
                                store_id,
                                month,
                            )
                        ]
                    )

                    growth = 0.0

                else:
                    previous_year = (
                        year - 1
                    )

                    source = (
                        actual_lookup[
                            (
                                store_id,
                                previous_year,
                                month,
                            )
                        ]
                    )

                    growth = (
                        YEAR_GROWTH_EXPECTATION[
                            year
                        ]
                    )

                month_noise = float(
                    rng.normal(
                        loc=1.0,
                        scale=0.025,
                    )
                )

                month_noise = float(
                    np.clip(
                        month_noise,
                        0.94,
                        1.06,
                    )
                )

                target_multiplier = (
                    (1.0 + growth)
                    * store_stretch
                    * month_noise
                )

                revenue_target = max(
                    float(
                        source[
                            "Revenue"
                        ]
                    )
                    * target_multiplier,
                    0.0,
                )

                profit_target = max(
                    float(
                        source[
                            "GrossProfit"
                        ]
                    )
                    * target_multiplier,
                    0.0,
                )

                orders_target = max(
                    int(
                        round(
                            float(
                                source[
                                    "Orders"
                                ]
                            )
                            * target_multiplier
                        )
                    ),
                    1,
                )

                rows.append(
                    {
                        "StoreMonthlyTargetId": (
                            target_id
                        ),
                        "StoreId": (
                            store_id
                        ),
                        "TargetYear": (
                            year
                        ),
                        "TargetMonth": (
                            month
                        ),
                        "RevenueTarget": money(
                            revenue_target
                        ),
                        "GrossProfitTarget": money(
                            profit_target
                        ),
                        "OrdersTarget": (
                            orders_target
                        ),
                    }
                )

                target_id += 1

    targets = pd.DataFrame(
        rows
    )

    validate_targets(
        targets=targets,
        stores=stores,
    )

    return targets


def validate_targets(
    targets: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    expected_rows = (
        len(stores)
        * 36
    )

    if (
        len(targets)
        != expected_rows
    ):
        raise ValueError(
            "Incorrect target count. "
            f"Expected {expected_rows}, "
            f"got {len(targets)}."
        )

    if not targets[
        "StoreMonthlyTargetId"
    ].is_unique:
        raise ValueError(
            "Duplicate target ID."
        )

    if targets.duplicated(
        subset=[
            "StoreId",
            "TargetYear",
            "TargetMonth",
        ]
    ).any():
        raise ValueError(
            "Duplicate Store x Month "
            "target."
        )

    if not targets[
        "StoreId"
    ].isin(
        stores[
            "StoreId"
        ]
    ).all():
        raise ValueError(
            "Invalid target StoreId."
        )

    if not targets[
        "TargetYear"
    ].between(
        2023,
        2025,
    ).all():
        raise ValueError(
            "Invalid TargetYear."
        )

    if not targets[
        "TargetMonth"
    ].between(
        1,
        12,
    ).all():
        raise ValueError(
            "Invalid TargetMonth."
        )

    revenue = pd.to_numeric(
        targets[
            "RevenueTarget"
        ]
    )

    profit = pd.to_numeric(
        targets[
            "GrossProfitTarget"
        ]
    )

    orders = pd.to_numeric(
        targets[
            "OrdersTarget"
        ]
    )

    if (
        revenue < 0
    ).any():
        raise ValueError(
            "Negative RevenueTarget."
        )

    if (
        profit < 0
    ).any():
        raise ValueError(
            "Negative GrossProfitTarget."
        )

    if (
        orders <= 0
    ).any():
        raise ValueError(
            "OrdersTarget must be "
            "positive."
        )

    store_counts = (
        targets.groupby(
            "StoreId"
        ).size()
    )

    if not (
        store_counts == 36
    ).all():
        raise ValueError(
            "Every store must have "
            "36 monthly targets."
        )

    print(
        "Targets validation "
        "completed successfully."
    )