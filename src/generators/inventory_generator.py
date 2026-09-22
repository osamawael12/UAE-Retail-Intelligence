"""
UAE Retail Intelligence Platform
Inventory Generator

Outputs:
- StoreProductInventory
- InventoryMovement

Rules:
- Every completed sales line creates one SALE movement.
- Every restockable return creates one RETURN movement.
- PURCHASE movements provide opening stock and replenishment.
- Limited DAMAGED and ADJUSTMENT movements add operational realism.
- Balanced TRANSFER_OUT / TRANSFER_IN pairs simulate store transfers.
- Inventory never becomes negative.
- Final CurrentStock exactly reconciles to the movement ledger.

This module does not write to SQL Server.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


MONEY_QUANTIZER = Decimal("0.0001")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def _create_inventory_config(
    stores: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:

    median_area = float(
        stores["FloorAreaSqM"].median()
    )

    rows = []

    for store in stores.itertuples(
        index=False
    ):
        store_factor = float(
            store.FloorAreaSqM
        ) / median_area

        store_factor = float(
            np.clip(
                store_factor,
                0.70,
                1.50,
            )
        )

        for product in products.itertuples(
            index=False
        ):
            popularity = float(
                product.PopularityScore
            )

            reorder_point = int(
                round(
                    (
                        4
                        + popularity * 16
                    )
                    * store_factor
                )
            )

            reorder_point = max(
                2,
                reorder_point,
            )

            reorder_quantity = int(
                round(
                    reorder_point
                    * (
                        2.2
                        + popularity
                    )
                )
            )

            reorder_quantity = max(
                reorder_quantity,
                reorder_point + 1,
            )

            rows.append(
                {
                    "StoreId": int(
                        store.StoreId
                    ),
                    "ProductId": int(
                        product.ProductId
                    ),
                    "ReorderPoint": (
                        reorder_point
                    ),
                    "ReorderQuantity": (
                        reorder_quantity
                    ),
                }
            )

    return pd.DataFrame(rows)


def _build_sales_events(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:

    # OrderId is intentionally retained here because
    # it is the merge key to SalesOrder.
    item_columns = [
        "OrderItemId",
        "OrderId",
        "ProductId",
        "Quantity",
        "UnitCost",
    ]

    missing = (
        set(item_columns)
        - set(order_items.columns)
    )

    if missing:
        raise ValueError(
            "sales_order_items.csv is missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    events = (
        order_items[
            item_columns
        ]
        .merge(
            orders[
                [
                    "OrderId",
                    "StoreId",
                    "OrderDateTime",
                    "OrderStatus",
                ]
            ],
            on="OrderId",
            how="inner",
            validate="many_to_one",
        )
    )

    events = events.loc[
        events["OrderStatus"]
        == "COMPLETED"
    ].copy()

    events["MovementDateTime"] = (
        pd.to_datetime(
            events["OrderDateTime"]
        )
    )

    events["MovementType"] = (
        "SALE"
    )

    events["QuantityChange"] = (
        -pd.to_numeric(
            events["Quantity"]
        ).astype(int)
    )

    events["ReturnItemId"] = (
        pd.NA
    )

    events["ReferenceNumber"] = (
        events["OrderItemId"]
        .astype(int)
        .map(
            lambda value:
                f"SALE-{value:010d}"
        )
    )

    events["Notes"] = (
        "Generated from completed sale"
    )

    return events[
        [
            "StoreId",
            "ProductId",
            "OrderItemId",
            "ReturnItemId",
            "MovementDateTime",
            "MovementType",
            "QuantityChange",
            "UnitCost",
            "ReferenceNumber",
            "Notes",
        ]
    ]


def _build_return_events(
    returns: pd.DataFrame,
    return_items: pd.DataFrame,
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
) -> pd.DataFrame:

    restockable = (
        return_items.loc[
            return_items["IsRestockable"]
            == 1
        ].copy()
    )

    columns = [
        "StoreId",
        "ProductId",
        "OrderItemId",
        "ReturnItemId",
        "MovementDateTime",
        "MovementType",
        "QuantityChange",
        "UnitCost",
        "ReferenceNumber",
        "Notes",
    ]

    if restockable.empty:
        return pd.DataFrame(
            columns=columns
        )

    events = (
        restockable[
            [
                "ReturnItemId",
                "ReturnId",
                "OrderItemId",
                "ReturnQuantity",
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
            how="inner",
            validate="many_to_one",
        )
        .merge(
            order_items[
                [
                    "OrderItemId",
                    "OrderId",
                    "ProductId",
                    "UnitCost",
                ]
            ],
            on="OrderItemId",
            how="inner",
            validate="many_to_one",
        )
        .merge(
            orders[
                [
                    "OrderId",
                    "StoreId",
                ]
            ],
            on="OrderId",
            how="inner",
            validate="many_to_one",
        )
    )

    events["MovementDateTime"] = (
        pd.to_datetime(
            events["ReturnDateTime"]
        )
    )

    events["MovementType"] = (
        "RETURN"
    )

    events["QuantityChange"] = (
        pd.to_numeric(
            events["ReturnQuantity"]
        ).astype(int)
    )

    events["ReferenceNumber"] = (
        events["ReturnItemId"]
        .astype(int)
        .map(
            lambda value:
                f"RETURN-{value:010d}"
        )
    )

    events["Notes"] = (
        "Restockable customer return"
    )

    return events[
        columns
    ]


def _generate_transaction_ledger(
    sales_events: pd.DataFrame,
    return_events: pd.DataFrame,
    inventory_config: pd.DataFrame,
    products: pd.DataFrame,
):

    config_lookup = {
        (
            int(row.StoreId),
            int(row.ProductId),
        ): (
            int(row.ReorderPoint),
            int(row.ReorderQuantity),
        )
        for row in (
            inventory_config.itertuples(
                index=False
            )
        )
    }

    cost_lookup = dict(
        zip(
            products[
                "ProductId"
            ].astype(int),
            products[
                "StandardCost"
            ],
        )
    )

    events = pd.concat(
        [
            sales_events,
            return_events,
        ],
        ignore_index=True,
    )

    type_order = {
        "RETURN": 0,
        "SALE": 1,
    }

    events["_TypeOrder"] = (
        events["MovementType"]
        .map(type_order)
        .fillna(9)
    )

    events = (
        events.sort_values(
            [
                "MovementDateTime",
                "_TypeOrder",
            ]
        )
        .drop(
            columns=[
                "_TypeOrder"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    stock = defaultdict(int)

    initialized = set()

    movements = []

    purchase_id = 1

    for event in events.itertuples(
        index=False
    ):
        store_id = int(
            event.StoreId
        )

        product_id = int(
            event.ProductId
        )

        key = (
            store_id,
            product_id,
        )

        reorder_point, reorder_quantity = (
            config_lookup[key]
        )

        timestamp = pd.Timestamp(
            event.MovementDateTime
        )

        if key not in initialized:
            opening_quantity = (
                reorder_point
                + reorder_quantity
            )

            opening_time = max(
                pd.Timestamp(
                    CONFIG.start_date
                ),
                timestamp
                - pd.Timedelta(
                    days=7
                ),
            )

            movements.append(
                {
                    "StoreId": store_id,
                    "ProductId": product_id,
                    "OrderItemId": None,
                    "ReturnItemId": None,
                    "MovementDateTime":
                        opening_time,
                    "MovementType":
                        "PURCHASE",
                    "QuantityChange":
                        opening_quantity,
                    "UnitCost": money(
                        cost_lookup[
                            product_id
                        ]
                    ),
                    "ReferenceNumber":
                        (
                            "PO-OPEN-"
                            f"{purchase_id:010d}"
                        ),
                    "Notes":
                        "Opening inventory",
                }
            )

            stock[key] += (
                opening_quantity
            )

            initialized.add(key)

            purchase_id += 1

        quantity_change = int(
            event.QuantityChange
        )

        if (
            event.MovementType
            == "SALE"
        ):
            required = abs(
                quantity_change
            )

            if stock[key] < required:
                shortage = (
                    required
                    - stock[key]
                )

                purchase_quantity = max(
                    reorder_quantity,
                    shortage
                    + reorder_point,
                )

                movements.append(
                    {
                        "StoreId":
                            store_id,
                        "ProductId":
                            product_id,
                        "OrderItemId":
                            None,
                        "ReturnItemId":
                            None,
                        "MovementDateTime":
                            (
                                timestamp
                                - pd.Timedelta(
                                    minutes=1
                                )
                            ),
                        "MovementType":
                            "PURCHASE",
                        "QuantityChange":
                            purchase_quantity,
                        "UnitCost":
                            money(
                                cost_lookup[
                                    product_id
                                ]
                            ),
                        "ReferenceNumber":
                            (
                                "PO-EMG-"
                                f"{purchase_id:010d}"
                            ),
                        "Notes":
                            (
                                "Emergency "
                                "replenishment"
                            ),
                    }
                )

                stock[key] += (
                    purchase_quantity
                )

                purchase_id += 1

        movements.append(
            {
                "StoreId": store_id,
                "ProductId": product_id,
                "OrderItemId": (
                    None
                    if pd.isna(
                        event.OrderItemId
                    )
                    else int(
                        event.OrderItemId
                    )
                ),
                "ReturnItemId": (
                    None
                    if pd.isna(
                        event.ReturnItemId
                    )
                    else int(
                        event.ReturnItemId
                    )
                ),
                "MovementDateTime":
                    timestamp,
                "MovementType":
                    str(
                        event.MovementType
                    ),
                "QuantityChange":
                    quantity_change,
                "UnitCost":
                    money(
                        event.UnitCost
                    ),
                "ReferenceNumber":
                    str(
                        event.ReferenceNumber
                    ),
                "Notes":
                    str(
                        event.Notes
                    ),
            }
        )

        stock[key] += (
            quantity_change
        )

        if stock[key] < 0:
            raise ValueError(
                "Negative stock after "
                f"{event.MovementType}: "
                f"{key}"
            )

        if (
            event.MovementType
            == "SALE"
            and stock[key]
            <= reorder_point
        ):
            movements.append(
                {
                    "StoreId":
                        store_id,
                    "ProductId":
                        product_id,
                    "OrderItemId":
                        None,
                    "ReturnItemId":
                        None,
                    "MovementDateTime":
                        (
                            timestamp
                            + pd.Timedelta(
                                minutes=1
                            )
                        ),
                    "MovementType":
                        "PURCHASE",
                    "QuantityChange":
                        reorder_quantity,
                    "UnitCost":
                        money(
                            cost_lookup[
                                product_id
                            ]
                        ),
                    "ReferenceNumber":
                        (
                            "PO-RPL-"
                            f"{purchase_id:010d}"
                        ),
                    "Notes":
                        (
                            "Automatic "
                            "replenishment"
                        ),
                }
            )

            stock[key] += (
                reorder_quantity
            )

            purchase_id += 1

    return (
        movements,
        stock,
    )


def _add_operational_movements(
    rng,
    movements,
    stock,
    inventory_config,
    products,
):

    cost_lookup = dict(
        zip(
            products[
                "ProductId"
            ].astype(int),
            products[
                "StandardCost"
            ],
        )
    )

    candidates = (
        inventory_config.sample(
            n=min(
                600,
                len(
                    inventory_config
                ),
            ),
            random_state=(
                CONFIG.random_seed
                + 910
            ),
        )
    )

    reference_id = 1

    for row in candidates.itertuples(
        index=False
    ):
        key = (
            int(row.StoreId),
            int(row.ProductId),
        )

        current = int(
            stock.get(
                key,
                0,
            )
        )

        if current <= 2:
            continue

        if rng.random() < 0.55:
            movement_type = (
                "DAMAGED"
            )

            quantity_change = -1
        else:
            movement_type = (
                "ADJUSTMENT"
            )

            quantity_change = int(
                rng.choice(
                    [-1, 1]
                )
            )

        if (
            current
            + quantity_change
            < 0
        ):
            continue

        movement_time = (
            pd.Timestamp(
                CONFIG.end_date
            )
            - pd.Timedelta(
                days=int(
                    rng.integers(
                        0,
                        90,
                    )
                ),
                hours=int(
                    rng.integers(
                        0,
                        12,
                    )
                ),
            )
        )

        movements.append(
            {
                "StoreId": key[0],
                "ProductId": key[1],
                "OrderItemId": None,
                "ReturnItemId": None,
                "MovementDateTime":
                    movement_time,
                "MovementType":
                    movement_type,
                "QuantityChange":
                    quantity_change,
                "UnitCost":
                    money(
                        cost_lookup[
                            key[1]
                        ]
                    ),
                "ReferenceNumber":
                    (
                        "OPS-"
                        f"{reference_id:08d}"
                    ),
                "Notes":
                    (
                        "Synthetic "
                        "operational event"
                    ),
            }
        )

        stock[key] = (
            current
            + quantity_change
        )

        reference_id += 1


def _add_transfers(
    rng,
    movements,
    stock,
    stores,
    products,
):

    store_ids = (
        stores["StoreId"]
        .astype(int)
        .to_numpy()
    )

    product_ids = (
        products["ProductId"]
        .astype(int)
        .to_numpy()
    )

    cost_lookup = dict(
        zip(
            products[
                "ProductId"
            ].astype(int),
            products[
                "StandardCost"
            ],
        )
    )

    transfer_number = 1
    attempts = 0

    while (
        transfer_number <= 250
        and attempts < 20_000
    ):
        attempts += 1

        product_id = int(
            rng.choice(
                product_ids
            )
        )

        source_store = int(
            rng.choice(
                store_ids
            )
        )

        destination_options = (
            store_ids[
                store_ids
                != source_store
            ]
        )

        destination_store = int(
            rng.choice(
                destination_options
            )
        )

        source_key = (
            source_store,
            product_id,
        )

        destination_key = (
            destination_store,
            product_id,
        )

        source_stock = int(
            stock.get(
                source_key,
                0,
            )
        )

        if source_stock < 5:
            continue

        quantity = int(
            rng.integers(
                1,
                min(
                    3,
                    source_stock - 2,
                )
                + 1,
            )
        )

        transfer_time = (
            pd.Timestamp(
                CONFIG.end_date
            )
            - pd.Timedelta(
                days=int(
                    rng.integers(
                        5,
                        300,
                    )
                ),
                hours=int(
                    rng.integers(
                        0,
                        12,
                    )
                ),
            )
        )

        reference = (
            "TRF-"
            f"{transfer_number:08d}"
        )

        cost = money(
            cost_lookup[
                product_id
            ]
        )

        movements.append(
            {
                "StoreId":
                    source_store,
                "ProductId":
                    product_id,
                "OrderItemId":
                    None,
                "ReturnItemId":
                    None,
                "MovementDateTime":
                    transfer_time,
                "MovementType":
                    "TRANSFER_OUT",
                "QuantityChange":
                    -quantity,
                "UnitCost":
                    cost,
                "ReferenceNumber":
                    reference,
                "Notes":
                    "Inter-store transfer",
            }
        )

        movements.append(
            {
                "StoreId":
                    destination_store,
                "ProductId":
                    product_id,
                "OrderItemId":
                    None,
                "ReturnItemId":
                    None,
                "MovementDateTime":
                    transfer_time,
                "MovementType":
                    "TRANSFER_IN",
                "QuantityChange":
                    quantity,
                "UnitCost":
                    cost,
                "ReferenceNumber":
                    reference,
                "Notes":
                    "Inter-store transfer",
            }
        )

        stock[source_key] = (
            source_stock
            - quantity
        )

        stock[destination_key] = (
            int(
                stock.get(
                    destination_key,
                    0,
                )
            )
            + quantity
        )

        transfer_number += 1


def generate_inventory_datasets(
    stores: pd.DataFrame,
    products: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    returns: pd.DataFrame,
    return_items: pd.DataFrame,
):

    rng = np.random.default_rng(
        CONFIG.random_seed + 900
    )

    inventory_config = (
        _create_inventory_config(
            stores=stores,
            products=products,
        )
    )

    sales_events = (
        _build_sales_events(
            orders=orders,
            order_items=order_items,
        )
    )

    return_events = (
        _build_return_events(
            returns=returns,
            return_items=return_items,
            order_items=order_items,
            orders=orders,
        )
    )

    (
        movements,
        stock,
    ) = _generate_transaction_ledger(
        sales_events=sales_events,
        return_events=return_events,
        inventory_config=(
            inventory_config
        ),
        products=products,
    )

    _add_operational_movements(
        rng=rng,
        movements=movements,
        stock=stock,
        inventory_config=(
            inventory_config
        ),
        products=products,
    )

    _add_transfers(
        rng=rng,
        movements=movements,
        stock=stock,
        stores=stores,
        products=products,
    )

    movement_df = pd.DataFrame(
        movements
    )

    movement_df[
        "MovementDateTime"
    ] = pd.to_datetime(
        movement_df[
            "MovementDateTime"
        ]
    )

    movement_df = (
        movement_df.sort_values(
            [
                "MovementDateTime",
                "StoreId",
                "ProductId",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    movement_df.insert(
        0,
        "InventoryMovementId",
        np.arange(
            1,
            len(
                movement_df
            )
            + 1,
            dtype=np.int64,
        ),
    )

    ledger_balances = (
        movement_df.groupby(
            [
                "StoreId",
                "ProductId",
            ],
            as_index=False,
        )[
            "QuantityChange"
        ]
        .sum()
        .rename(
            columns={
                "QuantityChange":
                    "CurrentStock"
            }
        )
    )

    inventory = (
        inventory_config.merge(
            ledger_balances,
            on=[
                "StoreId",
                "ProductId",
            ],
            how="left",
            validate="one_to_one",
        )
    )

    inventory[
        "CurrentStock"
    ] = (
        inventory[
            "CurrentStock"
        ]
        .fillna(0)
        .astype(int)
    )

    inventory[
        "LastUpdatedAt"
    ] = (
        pd.Timestamp(
            CONFIG.end_date
        )
        + pd.Timedelta(
            hours=23,
            minutes=59,
        )
    )

    validate_inventory_data(
        inventory=inventory,
        movements=movement_df,
        stores=stores,
        products=products,
        order_items=order_items,
        return_items=return_items,
    )

    return {
        "store_product_inventory":
            inventory,
        "inventory_movements":
            movement_df,
    }


def validate_inventory_data(
    inventory,
    movements,
    stores,
    products,
    order_items,
    return_items,
):

    expected_rows = (
        len(stores)
        * len(products)
    )

    if (
        len(inventory)
        != expected_rows
    ):
        raise ValueError(
            "Expected "
            f"{expected_rows:,} "
            "inventory records, got "
            f"{len(inventory):,}."
        )

    if inventory.duplicated(
        subset=[
            "StoreId",
            "ProductId",
        ]
    ).any():
        raise ValueError(
            "Duplicate Store/Product "
            "inventory record."
        )

    if (
        inventory[
            "CurrentStock"
        ]
        < 0
    ).any():
        raise ValueError(
            "Negative final stock."
        )

    if (
        inventory[
            "ReorderPoint"
        ]
        < 0
    ).any():
        raise ValueError(
            "Negative reorder point."
        )

    if (
        inventory[
            "ReorderQuantity"
        ]
        <= 0
    ).any():
        raise ValueError(
            "Invalid reorder quantity."
        )

    if not movements[
        "InventoryMovementId"
    ].is_unique:
        raise ValueError(
            "Duplicate "
            "InventoryMovementId."
        )

    valid_types = {
        "PURCHASE",
        "SALE",
        "RETURN",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "DAMAGED",
        "ADJUSTMENT",
    }

    if not movements[
        "MovementType"
    ].isin(
        valid_types
    ).all():
        raise ValueError(
            "Invalid movement type."
        )

    sale_movements = (
        movements.loc[
            movements[
                "MovementType"
            ]
            == "SALE"
        ]
    )

    if (
        len(sale_movements)
        != len(order_items)
    ):
        raise ValueError(
            "SALE movement count "
            "does not match "
            "SalesOrderItem count."
        )

    if (
        sale_movements[
            "OrderItemId"
        ].isna().any()
    ):
        raise ValueError(
            "SALE movement without "
            "OrderItemId."
        )

    sold_ids = set(
        order_items[
            "OrderItemId"
        ].astype(int)
    )

    movement_ids = set(
        sale_movements[
            "OrderItemId"
        ].astype(int)
    )

    if (
        sold_ids
        != movement_ids
    ):
        raise ValueError(
            "SALE movements do not map "
            "one-to-one to order items."
        )

    expected_return_ids = set(
        return_items.loc[
            return_items[
                "IsRestockable"
            ]
            == 1,
            "ReturnItemId",
        ].astype(int)
    )

    return_movements = (
        movements.loc[
            movements[
                "MovementType"
            ]
            == "RETURN"
        ]
    )

    actual_return_ids = set(
        return_movements[
            "ReturnItemId"
        ]
        .dropna()
        .astype(int)
    )

    if (
        expected_return_ids
        != actual_return_ids
    ):
        raise ValueError(
            "RETURN movements do not "
            "match restockable returns."
        )

    ledger = (
        movements.groupby(
            [
                "StoreId",
                "ProductId",
            ],
            as_index=False,
        )[
            "QuantityChange"
        ]
        .sum()
        .rename(
            columns={
                "QuantityChange":
                    "LedgerStock"
            }
        )
    )

    check = (
        inventory.merge(
            ledger,
            on=[
                "StoreId",
                "ProductId",
            ],
            how="left",
            validate="one_to_one",
        )
    )

    check[
        "LedgerStock"
    ] = (
        check[
            "LedgerStock"
        ]
        .fillna(0)
        .astype(int)
    )

    if not (
        check[
            "CurrentStock"
        ].astype(int)
        == check[
            "LedgerStock"
        ].astype(int)
    ).all():
        raise ValueError(
            "Final inventory does not "
            "reconcile with ledger."
        )

    print(
        "Inventory validation "
        "completed successfully."
    )