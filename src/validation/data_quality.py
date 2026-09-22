"""
UAE Retail Intelligence Platform
Full Data Quality Engine

Validates generated datasets before SQL Server bulk loading.

Checks:
- Required datasets
- Required columns
- Expected row counts
- Primary-key integrity
- Foreign-key integrity
- Date ranges
- Sales financial calculations
- Order header reconciliation
- Payment reconciliation
- Return integrity
- Refund reconciliation
- Inventory movement integrity
- Inventory balance reconciliation
- Monthly target integrity

Any critical error prevents the pipeline from proceeding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from config.generation_config import CONFIG


MONEY_QUANTIZER = Decimal("0.0001")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


@dataclass
class DQResult:
    check_name: str
    passed: bool
    details: str


@dataclass
class DataQualityReport:
    results: list[DQResult] = field(
        default_factory=list
    )

    def add(
        self,
        check_name: str,
        passed: bool,
        details: str,
    ) -> None:
        self.results.append(
            DQResult(
                check_name=check_name,
                passed=passed,
                details=details,
            )
        )

    @property
    def failed_count(self) -> int:
        return sum(
            not result.passed
            for result in self.results
        )

    @property
    def passed_count(self) -> int:
        return sum(
            result.passed
            for result in self.results
        )

    @property
    def is_valid(self) -> bool:
        return self.failed_count == 0


REQUIRED_FILES = {
    "emirates": "core_emirates.csv",
    "cities": "core_cities.csv",
    "stores": "core_stores.csv",
    "dates": "core_date_dimension.csv",
    "channels": "core_sales_channels.csv",
    "payment_methods": "core_payment_methods.csv",
    "employees": "core_employees.csv",

    "categories": "product_categories.csv",
    "subcategories": "product_subcategories.csv",
    "brands": "product_brands.csv",
    "suppliers": "product_suppliers_master.csv",
    "products": "product_products.csv",
    "product_suppliers": (
        "product_product_suppliers.csv"
    ),

    "customers": "customer_customers.csv",
    "customer_segments": (
        "customer_segment_history.csv"
    ),

    "promotions": "sales_promotions.csv",
    "promotion_products": (
        "sales_promotion_products.csv"
    ),
    "promotion_categories": (
        "sales_promotion_categories.csv"
    ),
    "promotion_stores": (
        "sales_promotion_stores.csv"
    ),

    "orders": "sales_orders.csv",
    "order_items": "sales_order_items.csv",
    "payments": "sales_order_payments.csv",

    "returns": "sales_returns.csv",
    "return_items": "sales_return_items.csv",
    "refunds": "sales_refunds.csv",

    "inventory": "inventory_store_product.csv",
    "inventory_movements": (
        "inventory_movements.csv"
    ),

    "targets": (
        "sales_store_monthly_targets.csv"
    ),
}


REQUIRED_COLUMNS = {
    "emirates": {
        "EmirateId",
        "EmirateCode",
        "EmirateName",
    },
    "cities": {
        "CityId",
        "EmirateId",
        "CityName",
    },
    "stores": {
        "StoreId",
        "CityId",
        "StoreCode",
    },
    "dates": {
        "DateKey",
        "FullDate",
        "YearNumber",
        "MonthNumber",
    },
    "employees": {
        "EmployeeId",
        "StoreId",
        "EmployeeCode",
    },
    "categories": {
        "CategoryId",
        "CategoryName",
    },
    "subcategories": {
        "SubcategoryId",
        "CategoryId",
    },
    "brands": {
        "BrandId",
        "BrandName",
    },
    "suppliers": {
        "SupplierId",
        "SupplierCode",
    },
    "products": {
        "ProductId",
        "SubcategoryId",
        "BrandId",
        "SKU",
    },
    "product_suppliers": {
        "ProductId",
        "SupplierId",
    },
    "customers": {
        "CustomerId",
        "CustomerCode",
        "RegistrationDate",
    },
    "customer_segments": {
        "CustomerSegmentHistoryId",
        "CustomerId",
        "SegmentName",
    },
    "promotions": {
        "PromotionId",
        "PromotionCode",
        "StartDate",
        "EndDate",
    },
    "orders": {
        "OrderId",
        "OrderNumber",
        "CustomerId",
        "StoreId",
        "SalesChannelId",
        "DateKey",
        "OrderDateTime",
        "GrossAmount",
        "DiscountAmount",
        "NetAmount",
        "VATAmount",
        "CustomerTotal",
    },
    "order_items": {
        "OrderItemId",
        "OrderId",
        "ProductId",
        "Quantity",
        "UnitPrice",
        "UnitCost",
        "GrossAmount",
        "DiscountAmount",
        "NetAmount",
        "VATRate",
        "VATAmount",
        "CustomerTotal",
        "LineCOGS",
    },
    "payments": {
        "OrderPaymentId",
        "OrderId",
        "PaymentMethodId",
        "PaymentAmount",
    },
    "returns": {
        "ReturnId",
        "OrderId",
        "StoreId",
        "DateKey",
        "ReturnDateTime",
    },
    "return_items": {
        "ReturnItemId",
        "ReturnId",
        "OrderItemId",
        "ReturnQuantity",
        "ReturnedNetAmount",
        "VATReversed",
        "RefundAmount",
    },
    "refunds": {
        "RefundId",
        "ReturnId",
        "PaymentMethodId",
        "RefundAmount",
    },
    "inventory": {
        "StoreId",
        "ProductId",
        "ReorderPoint",
        "ReorderQuantity",
        "CurrentStock",
    },
    "inventory_movements": {
        "InventoryMovementId",
        "StoreId",
        "ProductId",
        "MovementType",
        "QuantityChange",
    },
    "targets": {
        "StoreMonthlyTargetId",
        "StoreId",
        "TargetYear",
        "TargetMonth",
        "RevenueTarget",
        "GrossProfitTarget",
        "OrdersTarget",
    },
}


PRIMARY_KEYS = {
    "emirates": ["EmirateId"],
    "cities": ["CityId"],
    "stores": ["StoreId"],
    "dates": ["DateKey"],
    "employees": ["EmployeeId"],

    "categories": ["CategoryId"],
    "subcategories": ["SubcategoryId"],
    "brands": ["BrandId"],
    "suppliers": ["SupplierId"],
    "products": ["ProductId"],
    "product_suppliers": [
        "ProductId",
        "SupplierId",
    ],

    "customers": ["CustomerId"],
    "customer_segments": [
        "CustomerSegmentHistoryId"
    ],

    "promotions": ["PromotionId"],
    "promotion_products": [
        "PromotionId",
        "ProductId",
    ],
    "promotion_categories": [
        "PromotionId",
        "CategoryId",
    ],
    "promotion_stores": [
        "PromotionId",
        "StoreId",
    ],

    "orders": ["OrderId"],
    "order_items": ["OrderItemId"],
    "payments": ["OrderPaymentId"],

    "returns": ["ReturnId"],
    "return_items": ["ReturnItemId"],
    "refunds": ["RefundId"],

    "inventory": [
        "StoreId",
        "ProductId",
    ],
    "inventory_movements": [
        "InventoryMovementId"
    ],

    "targets": [
        "StoreMonthlyTargetId"
    ],
}


def load_all_datasets(
    data_directory: Path,
) -> dict[str, pd.DataFrame]:
    datasets = {}

    for name, file_name in (
        REQUIRED_FILES.items()
    ):
        path = (
            data_directory
            / file_name
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Required dataset missing: "
                f"{path}"
            )

        datasets[name] = pd.read_csv(
            path,
            low_memory=False,
        )

    return datasets


def check_required_columns(
    datasets,
    report,
):
    errors = []

    for name, required in (
        REQUIRED_COLUMNS.items()
    ):
        actual = set(
            datasets[name].columns
        )

        missing = (
            required - actual
        )

        if missing:
            errors.append(
                f"{name}: "
                + ", ".join(
                    sorted(missing)
                )
            )

    report.add(
        "Required columns",
        not errors,
        (
            "All required columns present"
            if not errors
            else "Missing -> "
            + "; ".join(errors)
        ),
    )


def check_primary_keys(
    datasets,
    report,
):
    errors = []

    for name, columns in (
        PRIMARY_KEYS.items()
    ):
        df = datasets[name]

        null_rows = (
            df[columns]
            .isna()
            .any(axis=1)
            .sum()
        )

        duplicate_rows = (
            df.duplicated(
                subset=columns
            ).sum()
        )

        if null_rows:
            errors.append(
                f"{name}: "
                f"{null_rows} NULL PK rows"
            )

        if duplicate_rows:
            errors.append(
                f"{name}: "
                f"{duplicate_rows} duplicate PK rows"
            )

    report.add(
        "Primary-key integrity",
        not errors,
        (
            "No NULL or duplicate PKs"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_expected_volumes(
    d,
    report,
):
    expected = {
        "emirates": 7,
        "stores": 25,
        "categories": 8,
        "brands": 60,
        "suppliers": 50,
        "products": 800,
        "customers": 25_000,
        "employees": 300,
        "orders": 100_000,
        "targets": 900,
        "dates": 1096,
    }

    errors = []

    for name, expected_count in (
        expected.items()
    ):
        actual = len(d[name])

        if actual != expected_count:
            errors.append(
                f"{name}: expected "
                f"{expected_count:,}, "
                f"got {actual:,}"
            )

    report.add(
        "Expected business volumes",
        not errors,
        (
            "Core project volumes match"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_foreign_keys(
    d,
    report,
):
    relationships = [
        (
            "cities",
            "EmirateId",
            "emirates",
            "EmirateId",
        ),
        (
            "stores",
            "CityId",
            "cities",
            "CityId",
        ),
        (
            "employees",
            "StoreId",
            "stores",
            "StoreId",
        ),
        (
            "subcategories",
            "CategoryId",
            "categories",
            "CategoryId",
        ),
        (
            "products",
            "SubcategoryId",
            "subcategories",
            "SubcategoryId",
        ),
        (
            "products",
            "BrandId",
            "brands",
            "BrandId",
        ),
        (
            "product_suppliers",
            "ProductId",
            "products",
            "ProductId",
        ),
        (
            "product_suppliers",
            "SupplierId",
            "suppliers",
            "SupplierId",
        ),
        (
            "customer_segments",
            "CustomerId",
            "customers",
            "CustomerId",
        ),
        (
            "promotion_products",
            "PromotionId",
            "promotions",
            "PromotionId",
        ),
        (
            "promotion_products",
            "ProductId",
            "products",
            "ProductId",
        ),
        (
            "promotion_categories",
            "PromotionId",
            "promotions",
            "PromotionId",
        ),
        (
            "promotion_categories",
            "CategoryId",
            "categories",
            "CategoryId",
        ),
        (
            "promotion_stores",
            "PromotionId",
            "promotions",
            "PromotionId",
        ),
        (
            "promotion_stores",
            "StoreId",
            "stores",
            "StoreId",
        ),
        (
            "orders",
            "CustomerId",
            "customers",
            "CustomerId",
        ),
        (
            "orders",
            "StoreId",
            "stores",
            "StoreId",
        ),
        (
            "order_items",
            "OrderId",
            "orders",
            "OrderId",
        ),
        (
            "order_items",
            "ProductId",
            "products",
            "ProductId",
        ),
        (
            "payments",
            "OrderId",
            "orders",
            "OrderId",
        ),
        (
            "returns",
            "OrderId",
            "orders",
            "OrderId",
        ),
        (
            "return_items",
            "ReturnId",
            "returns",
            "ReturnId",
        ),
        (
            "return_items",
            "OrderItemId",
            "order_items",
            "OrderItemId",
        ),
        (
            "refunds",
            "ReturnId",
            "returns",
            "ReturnId",
        ),
        (
            "inventory",
            "StoreId",
            "stores",
            "StoreId",
        ),
        (
            "inventory",
            "ProductId",
            "products",
            "ProductId",
        ),
        (
            "inventory_movements",
            "StoreId",
            "stores",
            "StoreId",
        ),
        (
            "inventory_movements",
            "ProductId",
            "products",
            "ProductId",
        ),
        (
            "targets",
            "StoreId",
            "stores",
            "StoreId",
        ),
    ]

    errors = []

    for (
        child,
        child_column,
        parent,
        parent_column,
    ) in relationships:
        values = (
            d[child][child_column]
            .dropna()
        )

        valid_values = set(
            d[parent][parent_column]
            .dropna()
        )

        orphan_count = int(
            (~values.isin(
                valid_values
            )).sum()
        )

        if orphan_count:
            errors.append(
                f"{child}.{child_column}: "
                f"{orphan_count} orphan rows"
            )

    report.add(
        "Foreign-key integrity",
        not errors,
        (
            "No orphan foreign keys"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_dates(
    d,
    report,
):
    errors = []

    calendar = d["dates"].copy()

    full_dates = pd.to_datetime(
        calendar["FullDate"]
    ).dt.date

    if (
        full_dates.min()
        != CONFIG.start_date
    ):
        errors.append(
            "DateDimension start date"
        )

    if (
        full_dates.max()
        != CONFIG.end_date
    ):
        errors.append(
            "DateDimension end date"
        )

    orders = d["orders"].copy()

    order_dates = pd.to_datetime(
        orders["OrderDateTime"]
    ).dt.date

    if (
        order_dates.min()
        < CONFIG.start_date
        or order_dates.max()
        > CONFIG.end_date
    ):
        errors.append(
            "Order outside simulation period"
        )

    customers = (
        d["customers"][
            [
                "CustomerId",
                "RegistrationDate",
            ]
        ].copy()
    )

    customers[
        "RegistrationDate"
    ] = pd.to_datetime(
        customers["RegistrationDate"]
    ).dt.date

    order_customer = (
        orders[
            [
                "CustomerId",
                "OrderDateTime",
            ]
        ]
        .merge(
            customers,
            on="CustomerId",
            how="left",
            validate="many_to_one",
        )
    )

    order_customer[
        "OrderDate"
    ] = pd.to_datetime(
        order_customer[
            "OrderDateTime"
        ]
    ).dt.date

    invalid_registration = (
        order_customer[
            "OrderDate"
        ]
        < order_customer[
            "RegistrationDate"
        ]
    )

    if invalid_registration.any():
        errors.append(
            "Purchase before customer registration"
        )

    report.add(
        "Date integrity",
        not errors,
        (
            "Dates are valid"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_sales_financials(
    d,
    report,
):
    items = d["order_items"]

    failures = {
        "Gross": 0,
        "Net": 0,
        "VAT": 0,
        "Total": 0,
        "COGS": 0,
    }

    for row in items.itertuples(
        index=False
    ):
        quantity = int(
            row.Quantity
        )

        unit_price = money(
            row.UnitPrice
        )

        unit_cost = money(
            row.UnitCost
        )

        gross = money(
            row.GrossAmount
        )

        discount = money(
            row.DiscountAmount
        )

        net = money(
            row.NetAmount
        )

        vat_rate = Decimal(
            str(row.VATRate)
        )

        vat = money(
            row.VATAmount
        )

        total = money(
            row.CustomerTotal
        )

        cogs = money(
            row.LineCOGS
        )

        if gross != money(
            unit_price * quantity
        ):
            failures["Gross"] += 1

        if (
            discount < 0
            or discount > gross
            or net != money(
                gross - discount
            )
        ):
            failures["Net"] += 1

        if vat != money(
            net * vat_rate
        ):
            failures["VAT"] += 1

        if total != money(
            net + vat
        ):
            failures["Total"] += 1

        if cogs != money(
            unit_cost * quantity
        ):
            failures["COGS"] += 1

    errors = [
        f"{name}={count:,}"
        for name, count in (
            failures.items()
        )
        if count
    ]

    report.add(
        "Sales financial calculations",
        not errors,
        (
            "All line calculations reconcile"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_order_reconciliation(
    d,
    report,
):
    orders = d["orders"]

    items = d["order_items"]

    columns = [
        "GrossAmount",
        "DiscountAmount",
        "NetAmount",
        "VATAmount",
        "CustomerTotal",
    ]

    item_totals = (
        items.groupby(
            "OrderId",
            as_index=False,
        )[columns]
        .sum()
    )

    merged = (
        orders[
            [
                "OrderId",
                *columns,
            ]
        ]
        .merge(
            item_totals,
            on="OrderId",
            how="left",
            suffixes=(
                "_Header",
                "_Items",
            ),
            validate="one_to_one",
        )
    )

    errors = []

    for column in columns:
        left = (
            merged[
                f"{column}_Header"
            ]
            .map(money)
        )

        right = (
            merged[
                f"{column}_Items"
            ]
            .map(money)
        )

        failures = int(
            (left != right).sum()
        )

        if failures:
            errors.append(
                f"{column}: "
                f"{failures:,}"
            )

    report.add(
        "Order header reconciliation",
        not errors,
        (
            "Headers equal order-item totals"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_payments(
    d,
    report,
):
    payment_totals = (
        d["payments"]
        .groupby(
            "OrderId",
            as_index=False,
        )[
            "PaymentAmount"
        ]
        .sum()
    )

    check = (
        d["orders"][
            [
                "OrderId",
                "CustomerTotal",
            ]
        ]
        .merge(
            payment_totals,
            on="OrderId",
            how="left",
            validate="one_to_one",
        )
    )

    missing = int(
        check[
            "PaymentAmount"
        ].isna().sum()
    )

    mismatch = int(
        (
            check[
                "CustomerTotal"
            ].map(money)
            != check[
                "PaymentAmount"
            ].map(money)
        ).sum()
    )

    passed = (
        missing == 0
        and mismatch == 0
    )

    report.add(
        "Payment reconciliation",
        passed,
        (
            "Payments equal order totals"
            if passed
            else (
                f"missing={missing:,}; "
                f"mismatch={mismatch:,}"
            )
        ),
    )


def check_returns(
    d,
    report,
):
    errors = []

    returns = d["returns"].copy()

    return_items = (
        d["return_items"].copy()
    )

    orders = (
        d["orders"][
            [
                "OrderId",
                "OrderDateTime",
            ]
        ].copy()
    )

    timing = (
        returns[
            [
                "ReturnId",
                "OrderId",
                "ReturnDateTime",
            ]
        ]
        .merge(
            orders,
            on="OrderId",
            how="left",
            validate="many_to_one",
        )
    )

    invalid_timing = int(
        (
            pd.to_datetime(
                timing[
                    "ReturnDateTime"
                ]
            )
            < pd.to_datetime(
                timing[
                    "OrderDateTime"
                ]
            )
        ).sum()
    )

    if invalid_timing:
        errors.append(
            "Return before sale="
            f"{invalid_timing:,}"
        )

    sold_quantities = (
        d["order_items"]
        .set_index(
            "OrderItemId"
        )[
            "Quantity"
        ]
        .astype(int)
    )

    returned = (
        return_items.groupby(
            "OrderItemId"
        )[
            "ReturnQuantity"
        ]
        .sum()
        .astype(int)
    )

    invalid_quantity = 0

    for (
        order_item_id,
        quantity,
    ) in returned.items():
        if (
            quantity
            > sold_quantities.loc[
                order_item_id
            ]
        ):
            invalid_quantity += 1

    if invalid_quantity:
        errors.append(
            "Over-returned items="
            f"{invalid_quantity:,}"
        )

    refunds = (
        d["refunds"]
        .groupby(
            "ReturnId",
            as_index=False,
        )[
            "RefundAmount"
        ]
        .sum()
    )

    refund_check = (
        returns[
            [
                "ReturnId",
                "TotalRefundAmount",
            ]
        ]
        .merge(
            refunds,
            on="ReturnId",
            how="left",
            validate="one_to_one",
        )
    )

    refund_mismatch = int(
        (
            refund_check[
                "TotalRefundAmount"
            ].map(money)
            != refund_check[
                "RefundAmount"
            ].map(money)
        ).sum()
    )

    if refund_mismatch:
        errors.append(
            "Refund mismatch="
            f"{refund_mismatch:,}"
        )

    report.add(
        "Returns and refunds",
        not errors,
        (
            "Returns and refunds are valid"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_inventory(
    d,
    report,
):
    errors = []

    inventory = d["inventory"]

    movements = (
        d["inventory_movements"]
    )

    expected_rows = (
        len(d["stores"])
        * len(d["products"])
    )

    if (
        len(inventory)
        != expected_rows
    ):
        errors.append(
            "Inventory grain expected "
            f"{expected_rows:,}, "
            f"got {len(inventory):,}"
        )

    if (
        pd.to_numeric(
            inventory[
                "CurrentStock"
            ]
        )
        < 0
    ).any():
        errors.append(
            "Negative CurrentStock"
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
        != len(
            d["order_items"]
        )
    ):
        errors.append(
            "SALE movement count mismatch"
        )

    expected_return_ids = set(
        d["return_items"].loc[
            d["return_items"][
                "IsRestockable"
            ]
            == 1,
            "ReturnItemId",
        ].astype(int)
    )

    actual_return_ids = set(
        movements.loc[
            movements[
                "MovementType"
            ]
            == "RETURN",
            "ReturnItemId",
        ]
        .dropna()
        .astype(int)
    )

    if (
        expected_return_ids
        != actual_return_ids
    ):
        errors.append(
            "RETURN movement mismatch"
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

    stock_check = (
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

    stock_check[
        "LedgerStock"
    ] = (
        stock_check[
            "LedgerStock"
        ]
        .fillna(0)
    )

    mismatch = int(
        (
            pd.to_numeric(
                stock_check[
                    "CurrentStock"
                ]
            ).astype(int)
            != pd.to_numeric(
                stock_check[
                    "LedgerStock"
                ]
            ).astype(int)
        ).sum()
    )

    if mismatch:
        errors.append(
            "Ledger mismatch="
            f"{mismatch:,}"
        )

    valid_signs = (
        (
            (
                movements[
                    "MovementType"
                ]
                .isin(
                    [
                        "PURCHASE",
                        "RETURN",
                        "TRANSFER_IN",
                    ]
                )
            )
            & (
                pd.to_numeric(
                    movements[
                        "QuantityChange"
                    ]
                )
                <= 0
            )
        )
        |
        (
            (
                movements[
                    "MovementType"
                ]
                .isin(
                    [
                        "SALE",
                        "TRANSFER_OUT",
                        "DAMAGED",
                    ]
                )
            )
            & (
                pd.to_numeric(
                    movements[
                        "QuantityChange"
                    ]
                )
                >= 0
            )
        )
    )

    bad_sign_count = int(
        valid_signs.sum()
    )

    if bad_sign_count:
        errors.append(
            "Invalid movement signs="
            f"{bad_sign_count:,}"
        )

    report.add(
        "Inventory integrity",
        not errors,
        (
            "Inventory ledger reconciles"
            if not errors
            else "; ".join(errors)
        ),
    )


def check_targets(
    d,
    report,
):
    targets = d["targets"]

    errors = []

    expected = (
        25 * 36
    )

    if len(targets) != expected:
        errors.append(
            f"expected {expected}, "
            f"got {len(targets)}"
        )

    duplicates = int(
        targets.duplicated(
            subset=[
                "StoreId",
                "TargetYear",
                "TargetMonth",
            ]
        ).sum()
    )

    if duplicates:
        errors.append(
            "duplicate Store/Month="
            f"{duplicates}"
        )

    counts = (
        targets.groupby(
            "StoreId"
        ).size()
    )

    invalid_store_counts = int(
        (
            counts != 36
        ).sum()
    )

    if invalid_store_counts:
        errors.append(
            "stores without 36 months="
            f"{invalid_store_counts}"
        )

    if (
        pd.to_numeric(
            targets[
                "RevenueTarget"
            ]
        )
        < 0
    ).any():
        errors.append(
            "negative revenue targets"
        )

    if (
        pd.to_numeric(
            targets[
                "GrossProfitTarget"
            ]
        )
        < 0
    ).any():
        errors.append(
            "negative profit targets"
        )

    report.add(
        "Monthly targets",
        not errors,
        (
            "900 unique monthly targets"
            if not errors
            else "; ".join(errors)
        ),
    )


def run_data_quality(
    data_directory: Path,
) -> tuple[
    DataQualityReport,
    dict[str, pd.DataFrame],
]:
    datasets = load_all_datasets(
        data_directory
    )

    report = DataQualityReport()

    check_required_columns(
        datasets,
        report,
    )

    check_primary_keys(
        datasets,
        report,
    )

    check_expected_volumes(
        datasets,
        report,
    )

    check_foreign_keys(
        datasets,
        report,
    )

    check_dates(
        datasets,
        report,
    )

    check_sales_financials(
        datasets,
        report,
    )

    check_order_reconciliation(
        datasets,
        report,
    )

    check_payments(
        datasets,
        report,
    )

    check_returns(
        datasets,
        report,
    )

    check_inventory(
        datasets,
        report,
    )

    check_targets(
        datasets,
        report,
    )

    return (
        report,
        datasets,
    )