"""
UAE Retail Intelligence Platform
Synthetic Returns Generator

Generates:
- Return
- ReturnItem
- Refund

Return probability is influenced by:
- Product base return probability
- Customer return behaviour
- Product category
- Quantity purchased
- Controlled synthetic quality anomaly

Business rules:
- Return occurs after the original sale.
- Return quantity never exceeds sold quantity.
- Returned merchandise value is calculated from the
  original sales line after discount.
- VAT reversal uses the historical line VAT rate.
- Refund includes returned net merchandise value plus
  reversed VAT.
- Refund transaction occurs on or after the return.
- Rejected returns are not generated in this synthetic
  transaction dataset; generated returns are completed.

This module does not write to SQL Server.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


MONEY_QUANTIZER = Decimal("0.0001")


CATEGORY_RETURN_MULTIPLIER = {
    "Fashion": 1.25,
    "Electronics": 1.08,
    "Beauty": 0.80,
    "Home": 0.90,
    "Sports": 1.05,
    "Grocery": 0.30,
    "Toys": 0.85,
    "Lifestyle": 0.90,
}


RETURN_REASON_CONFIG = {
    "Fashion": {
        "SIZE_FIT_ISSUE": 0.43,
        "CHANGED_MIND": 0.23,
        "DEFECTIVE_PRODUCT": 0.12,
        "WRONG_ITEM": 0.10,
        "DAMAGED_PRODUCT": 0.07,
        "OTHER": 0.05,
    },
    "Electronics": {
        "DEFECTIVE_PRODUCT": 0.38,
        "CHANGED_MIND": 0.20,
        "DAMAGED_PRODUCT": 0.16,
        "WRONG_ITEM": 0.12,
        "OTHER": 0.14,
    },
    "Beauty": {
        "CHANGED_MIND": 0.30,
        "WRONG_ITEM": 0.20,
        "DAMAGED_PRODUCT": 0.15,
        "DEFECTIVE_PRODUCT": 0.15,
        "OTHER": 0.20,
    },
    "Home": {
        "DAMAGED_PRODUCT": 0.27,
        "CHANGED_MIND": 0.25,
        "DEFECTIVE_PRODUCT": 0.18,
        "WRONG_ITEM": 0.15,
        "OTHER": 0.15,
    },
    "Sports": {
        "SIZE_FIT_ISSUE": 0.31,
        "CHANGED_MIND": 0.24,
        "DEFECTIVE_PRODUCT": 0.16,
        "WRONG_ITEM": 0.12,
        "DAMAGED_PRODUCT": 0.10,
        "OTHER": 0.07,
    },
    "Grocery": {
        "DAMAGED_PRODUCT": 0.30,
        "WRONG_ITEM": 0.25,
        "DEFECTIVE_PRODUCT": 0.20,
        "OTHER": 0.25,
    },
    "Toys": {
        "DEFECTIVE_PRODUCT": 0.27,
        "CHANGED_MIND": 0.24,
        "DAMAGED_PRODUCT": 0.18,
        "WRONG_ITEM": 0.15,
        "OTHER": 0.16,
    },
    "Lifestyle": {
        "CHANGED_MIND": 0.30,
        "DEFECTIVE_PRODUCT": 0.20,
        "WRONG_ITEM": 0.16,
        "DAMAGED_PRODUCT": 0.14,
        "OTHER": 0.20,
    },
}


NON_RESTOCKABLE_REASONS = {
    "DEFECTIVE_PRODUCT",
    "DAMAGED_PRODUCT",
}


QUALITY_ANOMALY_START = pd.Timestamp(
    "2024-07-01"
).date()

QUALITY_ANOMALY_END = pd.Timestamp(
    "2024-09-30"
).date()

QUALITY_ANOMALY_PRODUCT_COUNT = 6

QUALITY_ANOMALY_MULTIPLIER = 3.25


def money(
    value: float | Decimal,
) -> Decimal:
    return Decimal(
        str(value)
    ).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def _choose_return_reason(
    rng: np.random.Generator,
    category_name: str,
    force_quality_issue: bool,
) -> str:
    if force_quality_issue:
        return str(
            rng.choice(
                [
                    "DEFECTIVE_PRODUCT",
                    "DAMAGED_PRODUCT",
                ],
                p=[
                    0.82,
                    0.18,
                ],
            )
        )

    config = RETURN_REASON_CONFIG[
        category_name
    ]

    reasons = list(
        config.keys()
    )

    probabilities = np.array(
        list(
            config.values()
        ),
        dtype=np.float64,
    )

    probabilities = (
        probabilities
        / probabilities.sum()
    )

    return str(
        rng.choice(
            reasons,
            p=probabilities,
        )
    )


def _return_delay_days(
    rng: np.random.Generator,
    category_name: str,
) -> int:
    if category_name == "Electronics":
        minimum = 1
        maximum = 21
    elif category_name == "Fashion":
        minimum = 1
        maximum = 30
    elif category_name == "Grocery":
        minimum = 1
        maximum = 7
    else:
        minimum = 1
        maximum = 25

    raw_delay = int(
        rng.gamma(
            shape=2.2,
            scale=4.0,
        )
    ) + minimum

    return int(
        np.clip(
            raw_delay,
            minimum,
            maximum,
        )
    )


def _return_quantity(
    rng: np.random.Generator,
    sold_quantity: int,
) -> int:
    if sold_quantity <= 1:
        return 1

    if rng.random() < 0.72:
        return 1

    return int(
        rng.integers(
            1,
            sold_quantity + 1,
        )
    )


def _returned_net_amount(
    line_net_amount: Decimal,
    sold_quantity: int,
    return_quantity: int,
) -> Decimal:
    if sold_quantity <= 0:
        raise ValueError(
            "Sold quantity must be positive."
        )

    return money(
        line_net_amount
        * Decimal(
            return_quantity
        )
        / Decimal(
            sold_quantity
        )
    )


def _select_quality_anomaly_products(
    products: pd.DataFrame,
    subcategories: pd.DataFrame,
    categories: pd.DataFrame,
) -> set[int]:
    product_categories = (
        products[
            [
                "ProductId",
                "SubcategoryId",
                "PopularityScore",
            ]
        ]
        .merge(
            subcategories[
                [
                    "SubcategoryId",
                    "CategoryId",
                ]
            ],
            on="SubcategoryId",
            how="left",
            validate="many_to_one",
        )
        .merge(
            categories[
                [
                    "CategoryId",
                    "CategoryName",
                ]
            ],
            on="CategoryId",
            how="left",
            validate="many_to_one",
        )
    )

    fashion = (
        product_categories.loc[
            product_categories[
                "CategoryName"
            ]
            == "Fashion"
        ]
        .sort_values(
            [
                "PopularityScore",
                "ProductId",
            ],
            ascending=[
                False,
                True,
            ],
        )
    )

    if (
        len(fashion)
        < QUALITY_ANOMALY_PRODUCT_COUNT
    ):
        raise ValueError(
            "Not enough Fashion products "
            "for quality anomaly."
        )

    return set(
        fashion.head(
            QUALITY_ANOMALY_PRODUCT_COUNT
        )[
            "ProductId"
        ].astype(int)
    )


def generate_return_datasets(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    customers: pd.DataFrame,
    customer_profiles: pd.DataFrame,
    products: pd.DataFrame,
    subcategories: pd.DataFrame,
    categories: pd.DataFrame,
    payment_methods: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(
        CONFIG.random_seed + 800
    )

    orders = orders.copy()
    order_items = order_items.copy()

    orders[
        "OrderDateTime"
    ] = pd.to_datetime(
        orders[
            "OrderDateTime"
        ]
    )

    customer_behavior = (
        customers[
            [
                "CustomerId",
            ]
        ]
        .merge(
            customer_profiles[
                [
                    "CustomerId",
                    "ReturnMultiplier",
                ]
            ],
            on="CustomerId",
            how="inner",
            validate="one_to_one",
        )
    )

    product_details = (
        products[
            [
                "ProductId",
                "SubcategoryId",
                "BaseReturnProbability",
            ]
        ]
        .merge(
            subcategories[
                [
                    "SubcategoryId",
                    "CategoryId",
                ]
            ],
            on="SubcategoryId",
            how="left",
            validate="many_to_one",
        )
        .merge(
            categories[
                [
                    "CategoryId",
                    "CategoryName",
                ]
            ],
            on="CategoryId",
            how="left",
            validate="many_to_one",
        )
    )

    sales_lines = (
        order_items.merge(
            orders[
                [
                    "OrderId",
                    "CustomerId",
                    "StoreId",
                    "OrderDateTime",
                    "OrderStatus",
                ]
            ],
            on="OrderId",
            how="inner",
            validate="many_to_one",
        )
        .merge(
            customer_behavior,
            on="CustomerId",
            how="inner",
            validate="many_to_one",
        )
        .merge(
            product_details,
            on="ProductId",
            how="inner",
            validate="many_to_one",
        )
    )

    sales_lines = sales_lines.loc[
        sales_lines[
            "OrderStatus"
        ]
        == "COMPLETED"
    ].copy()

    anomaly_product_ids = (
        _select_quality_anomaly_products(
            products=products,
            subcategories=subcategories,
            categories=categories,
        )
    )

    return_rows = []
    return_item_rows = []
    refund_rows = []

    next_return_id = 1
    next_return_item_id = 1
    next_refund_id = 1

    payment_method_ids = (
        payment_methods[
            "PaymentMethodId"
        ]
        .astype(int)
        .to_numpy()
    )

    for line in sales_lines.itertuples(
        index=False
    ):
        order_date = (
            pd.Timestamp(
                line.OrderDateTime
            ).date()
        )

        base_probability = float(
            line.BaseReturnProbability
        )

        customer_multiplier = float(
            line.ReturnMultiplier
        )

        category_name = str(
            line.CategoryName
        )

        category_multiplier = (
            CATEGORY_RETURN_MULTIPLIER[
                category_name
            ]
        )

        quantity_multiplier = (
            1.0
            + min(
                max(
                    int(
                        line.Quantity
                    )
                    - 1,
                    0,
                )
                * 0.05,
                0.15,
            )
        )

        is_quality_anomaly = (
            int(
                line.ProductId
            )
            in anomaly_product_ids
            and QUALITY_ANOMALY_START
            <= order_date
            <= QUALITY_ANOMALY_END
        )

        anomaly_multiplier = (
            QUALITY_ANOMALY_MULTIPLIER
            if is_quality_anomaly
            else 1.0
        )

        return_probability = (
            base_probability
            * customer_multiplier
            * category_multiplier
            * quantity_multiplier
            * anomaly_multiplier
        )

        return_probability = float(
            np.clip(
                return_probability,
                0.001,
                0.65,
            )
        )

        if (
            rng.random()
            >= return_probability
        ):
            continue

        sold_quantity = int(
            line.Quantity
        )

        return_quantity = (
            _return_quantity(
                rng=rng,
                sold_quantity=sold_quantity,
            )
        )

        delay_days = (
            _return_delay_days(
                rng=rng,
                category_name=(
                    category_name
                ),
            )
        )

        return_datetime = (
            pd.Timestamp(
                line.OrderDateTime
            )
            + pd.Timedelta(
                days=delay_days,
                hours=int(
                    rng.integers(
                        1,
                        10,
                    )
                ),
                minutes=int(
                    rng.integers(
                        0,
                        60,
                    )
                ),
            )
        )

        # Transactions after the simulation boundary
        # are outside the analytical period.
        if (
            return_datetime.date()
            > CONFIG.end_date
        ):
            continue

        return_reason = (
            _choose_return_reason(
                rng=rng,
                category_name=(
                    category_name
                ),
                force_quality_issue=(
                    is_quality_anomaly
                ),
            )
        )

        if (
            return_reason
            in NON_RESTOCKABLE_REASONS
        ):
            is_restockable = 0
        else:
            is_restockable = int(
                rng.random()
                < 0.90
            )

        line_net_amount = money(
            line.NetAmount
        )

        returned_net = (
            _returned_net_amount(
                line_net_amount=(
                    line_net_amount
                ),
                sold_quantity=(
                    sold_quantity
                ),
                return_quantity=(
                    return_quantity
                ),
            )
        )

        vat_rate = Decimal(
            str(
                line.VATRate
            )
        )

        vat_reversed = money(
            returned_net
            * vat_rate
        )

        refund_amount = money(
            returned_net
            + vat_reversed
        )

        return_id = (
            next_return_id
        )

        return_item_id = (
            next_return_item_id
        )

        refund_id = (
            next_refund_id
        )

        date_key = int(
            return_datetime.strftime(
                "%Y%m%d"
            )
        )

        return_rows.append(
            {
                "ReturnId": (
                    return_id
                ),
                "ReturnNumber": (
                    f"RET"
                    f"{return_id:09d}"
                ),
                "OrderId": int(
                    line.OrderId
                ),
                "StoreId": int(
                    line.StoreId
                ),
                "DateKey": (
                    date_key
                ),
                "ReturnDateTime": (
                    return_datetime
                ),
                "ReturnStatus": (
                    "COMPLETED"
                ),
                "TotalReturnNetAmount": (
                    returned_net
                ),
                "TotalVATReversed": (
                    vat_reversed
                ),
                "TotalRefundAmount": (
                    refund_amount
                ),
            }
        )

        return_item_rows.append(
            {
                "ReturnItemId": (
                    return_item_id
                ),
                "ReturnId": (
                    return_id
                ),
                "OrderItemId": int(
                    line.OrderItemId
                ),
                "ReturnQuantity": (
                    return_quantity
                ),
                "ReturnReason": (
                    return_reason
                ),
                "ReturnedNetAmount": (
                    returned_net
                ),
                "VATReversed": (
                    vat_reversed
                ),
                "RefundAmount": (
                    refund_amount
                ),
                "IsRestockable": (
                    is_restockable
                ),
            }
        )

        payment_method_id = int(
            rng.choice(
                payment_method_ids
            )
        )

        refund_datetime = (
            return_datetime
            + pd.Timedelta(
                minutes=int(
                    rng.integers(
                        5,
                        181,
                    )
                )
            )
        )

        refund_rows.append(
            {
                "RefundId": (
                    refund_id
                ),
                "ReturnId": (
                    return_id
                ),
                "PaymentMethodId": (
                    payment_method_id
                ),
                "RefundAmount": (
                    refund_amount
                ),
                "RefundDateTime": (
                    refund_datetime
                ),
                "RefundReference": (
                    f"REF"
                    f"{refund_id:010d}"
                ),
                "RefundStatus": (
                    "COMPLETED"
                ),
            }
        )

        next_return_id += 1
        next_return_item_id += 1
        next_refund_id += 1

    returns = pd.DataFrame(
        return_rows
    )

    return_items = pd.DataFrame(
        return_item_rows
    )

    refunds = pd.DataFrame(
        refund_rows
    )

    if returns.empty:
        raise ValueError(
            "No returns were generated."
        )

    datasets = {
        "returns": returns,
        "return_items": (
            return_items
        ),
        "refunds": refunds,
    }

    validate_return_data(
        datasets=datasets,
        orders=orders,
        order_items=order_items,
        products=products,
        subcategories=subcategories,
        categories=categories,
    )

    anomaly_manifest = (
        pd.DataFrame(
            {
                "ProductId": sorted(
                    anomaly_product_ids
                ),
                "AnomalyType": (
                    "TEMPORARY_QUALITY_ISSUE"
                ),
                "StartDate": (
                    QUALITY_ANOMALY_START
                ),
                "EndDate": (
                    QUALITY_ANOMALY_END
                ),
                "Multiplier": (
                    QUALITY_ANOMALY_MULTIPLIER
                ),
            }
        )
    )

    datasets[
        "return_anomaly_manifest"
    ] = anomaly_manifest

    return datasets


def validate_return_data(
    datasets: dict[str, pd.DataFrame],
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    subcategories: pd.DataFrame,
    categories: pd.DataFrame,
) -> None:
    returns = datasets[
        "returns"
    ]

    return_items = datasets[
        "return_items"
    ]

    refunds = datasets[
        "refunds"
    ]

    unique_checks = [
        (
            returns,
            "ReturnId",
        ),
        (
            returns,
            "ReturnNumber",
        ),
        (
            return_items,
            "ReturnItemId",
        ),
        (
            refunds,
            "RefundId",
        ),
        (
            refunds,
            "RefundReference",
        ),
    ]

    for (
        dataframe,
        column,
    ) in unique_checks:
        if not dataframe[
            column
        ].is_unique:
            raise ValueError(
                f"Duplicate "
                f"{column}."
            )

    if not returns[
        "OrderId"
    ].isin(
        orders[
            "OrderId"
        ]
    ).all():
        raise ValueError(
            "Return references "
            "invalid OrderId."
        )

    if not return_items[
        "ReturnId"
    ].isin(
        returns[
            "ReturnId"
        ]
    ).all():
        raise ValueError(
            "Orphan ReturnItem."
        )

    if not return_items[
        "OrderItemId"
    ].isin(
        order_items[
            "OrderItemId"
        ]
    ).all():
        raise ValueError(
            "ReturnItem references "
            "invalid OrderItemId."
        )

    if not refunds[
        "ReturnId"
    ].isin(
        returns[
            "ReturnId"
        ]
    ).all():
        raise ValueError(
            "Orphan Refund."
        )

    original_quantities = (
        order_items.set_index(
            "OrderItemId"
        )[
            "Quantity"
        ]
        .astype(int)
    )

    returned_quantities = (
        return_items.groupby(
            "OrderItemId"
        )[
            "ReturnQuantity"
        ]
        .sum()
    )

    for (
        order_item_id,
        returned_quantity,
    ) in returned_quantities.items():
        sold_quantity = int(
            original_quantities.loc[
                order_item_id
            ]
        )

        if (
            int(
                returned_quantity
            )
            > sold_quantity
        ):
            raise ValueError(
                "Returned quantity exceeds "
                f"sold quantity for "
                f"OrderItemId "
                f"{order_item_id}."
            )

    return_order_dates = (
        returns[
            [
                "ReturnId",
                "OrderId",
                "ReturnDateTime",
            ]
        ]
        .merge(
            orders[
                [
                    "OrderId",
                    "OrderDateTime",
                ]
            ],
            on="OrderId",
            how="left",
            validate="many_to_one",
        )
    )

    return_order_dates[
        "ReturnDateTime"
    ] = pd.to_datetime(
        return_order_dates[
            "ReturnDateTime"
        ]
    )

    return_order_dates[
        "OrderDateTime"
    ] = pd.to_datetime(
        return_order_dates[
            "OrderDateTime"
        ]
    )

    invalid_dates = (
        return_order_dates[
            "ReturnDateTime"
        ]
        < return_order_dates[
            "OrderDateTime"
        ]
    )

    if invalid_dates.any():
        raise ValueError(
            "Return before sale detected."
        )

    if (
        pd.to_datetime(
            returns[
                "ReturnDateTime"
            ]
        ).dt.date
        > CONFIG.end_date
    ).any():
        raise ValueError(
            "Return outside simulation "
            "period."
        )

    if (
        return_items[
            "ReturnQuantity"
        ]
        <= 0
    ).any():
        raise ValueError(
            "Invalid return quantity."
        )

    valid_reasons = set()

    for config in (
        RETURN_REASON_CONFIG.values()
    ):
        valid_reasons.update(
            config.keys()
        )

    if not return_items[
        "ReturnReason"
    ].isin(
        valid_reasons
    ).all():
        raise ValueError(
            "Invalid return reason."
        )

    header_item_check = (
        returns[
            [
                "ReturnId",
                "TotalReturnNetAmount",
                "TotalVATReversed",
                "TotalRefundAmount",
            ]
        ]
        .merge(
            return_items[
                [
                    "ReturnId",
                    "ReturnedNetAmount",
                    "VATReversed",
                    "RefundAmount",
                ]
            ],
            on="ReturnId",
            how="inner",
            validate="one_to_one",
        )
    )

    comparisons = [
        (
            "TotalReturnNetAmount",
            "ReturnedNetAmount",
        ),
        (
            "TotalVATReversed",
            "VATReversed",
        ),
        (
            "TotalRefundAmount",
            "RefundAmount",
        ),
    ]

    for left, right in comparisons:
        left_values = (
            header_item_check[
                left
            ].map(money)
        )

        right_values = (
            header_item_check[
                right
            ].map(money)
        )

        if not (
            left_values
            == right_values
        ).all():
            raise ValueError(
                f"Return reconciliation "
                f"failed: {left}."
            )

    refund_check = (
        returns[
            [
                "ReturnId",
                "TotalRefundAmount",
            ]
        ]
        .merge(
            refunds[
                [
                    "ReturnId",
                    "RefundAmount",
                ]
            ],
            on="ReturnId",
            how="inner",
            validate="one_to_one",
        )
    )

    if (
        len(refund_check)
        != len(returns)
    ):
        raise ValueError(
            "Every completed return must "
            "have one refund."
        )

    expected_refunds = (
        refund_check[
            "TotalRefundAmount"
        ].map(money)
    )

    actual_refunds = (
        refund_check[
            "RefundAmount"
        ].map(money)
    )

    if not (
        expected_refunds
        == actual_refunds
    ).all():
        raise ValueError(
            "Refund reconciliation failed."
        )

    refund_dates = (
        refunds[
            [
                "ReturnId",
                "RefundDateTime",
            ]
        ]
        .merge(
            returns[
                [
                    "ReturnId",
                    "ReturnDateTime",
                ]
            ],
            on="ReturnId",
            how="left",
            validate="one_to_one",
        )
    )

    if (
        pd.to_datetime(
            refund_dates[
                "RefundDateTime"
            ]
        )
        < pd.to_datetime(
            refund_dates[
                "ReturnDateTime"
            ]
        )
    ).any():
        raise ValueError(
            "Refund before return detected."
        )

    print(
        "Returns validation completed "
        "successfully."
    )