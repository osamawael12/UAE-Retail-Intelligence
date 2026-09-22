"""
UAE Retail Intelligence Platform
SQL Server Bulk Loader

Loads validated CSV datasets into the existing SQL Server schema.

Important:
- Existing SQL tables are preserved.
- PK/FK/CHECK constraints remain active.
- Data is loaded in dependency order.
- Explicit identity values are loaded using IDENTITY_INSERT.
- The complete load runs inside one database transaction.
- If any table fails, the transaction is rolled back.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine


@dataclass(frozen=True)
class LoadSpec:
    file_name: str
    schema: str
    table: str
    columns: tuple[str, ...]
    identity_column: str | None = None
    batch_size: int = 2000

    @property
    def full_table_name(self) -> str:
        return (
            f"[{self.schema}]"
            f".[{self.table}]"
        )


LOAD_PLAN: tuple[LoadSpec, ...] = (
    LoadSpec(
        "core_emirates.csv",
        "core",
        "Emirate",
        (
            "EmirateId",
            "EmirateCode",
            "EmirateName",
            "IsActive",
        ),
        "EmirateId",
    ),
    LoadSpec(
        "core_cities.csv",
        "core",
        "City",
        (
            "CityId",
            "EmirateId",
            "CityName",
            "IsActive",
        ),
        "CityId",
    ),
    LoadSpec(
        "core_date_dimension.csv",
        "core",
        "DateDimension",
        (
            "DateKey",
            "FullDate",
            "DayNumber",
            "DayName",
            "DayOfWeekNumber",
            "WeekOfYear",
            "MonthNumber",
            "MonthName",
            "QuarterNumber",
            "YearNumber",
            "IsWeekend",
            "IsRamadan",
            "IsEidAlFitr",
            "IsEidAlAdha",
            "IsWhiteFriday",
            "IsEidAlEtihad",
            "IsSummer",
            "IsYearEndSeason",
        ),
    ),
    LoadSpec(
        "core_sales_channels.csv",
        "core",
        "SalesChannel",
        (
            "SalesChannelId",
            "ChannelCode",
            "ChannelName",
            "IsActive",
        ),
        "SalesChannelId",
    ),
    LoadSpec(
        "core_payment_methods.csv",
        "core",
        "PaymentMethod",
        (
            "PaymentMethodId",
            "PaymentMethodCode",
            "PaymentMethodName",
            "IsActive",
        ),
        "PaymentMethodId",
    ),
    LoadSpec(
        "core_stores.csv",
        "core",
        "Store",
        (
            "StoreId",
            "CityId",
            "StoreCode",
            "StoreName",
            "OpenDate",
            "StoreType",
            "FloorAreaSqM",
            "IsActive",
        ),
        "StoreId",
    ),
    LoadSpec(
        "core_employees.csv",
        "core",
        "Employee",
        (
            "EmployeeId",
            "StoreId",
            "EmployeeCode",
            "FirstName",
            "LastName",
            "JobTitle",
            "HireDate",
            "TerminationDate",
            "Email",
            "IsActive",
        ),
        "EmployeeId",
    ),

    LoadSpec(
        "product_categories.csv",
        "product",
        "Category",
        (
            "CategoryId",
            "CategoryName",
            "IsActive",
        ),
        "CategoryId",
    ),
    LoadSpec(
        "product_subcategories.csv",
        "product",
        "Subcategory",
        (
            "SubcategoryId",
            "CategoryId",
            "SubcategoryName",
            "IsActive",
        ),
        "SubcategoryId",
    ),
    LoadSpec(
        "product_brands.csv",
        "product",
        "Brand",
        (
            "BrandId",
            "BrandName",
            "IsActive",
        ),
        "BrandId",
    ),
    LoadSpec(
        "product_suppliers_master.csv",
        "product",
        "Supplier",
        (
            "SupplierId",
            "SupplierCode",
            "SupplierName",
            "ContactEmail",
            "ContactPhone",
            "IsActive",
        ),
        "SupplierId",
    ),
    LoadSpec(
        "product_products.csv",
        "product",
        "Product",
        (
            "ProductId",
            "SubcategoryId",
            "BrandId",
            "SKU",
            "ProductName",
            "BaseSellingPrice",
            "StandardCost",
            "DefaultVATRate",
            "PopularityScore",
            "SeasonalityProfile",
            "BaseReturnProbability",
            "LaunchDate",
            "DiscontinuedDate",
            "IsActive",
        ),
        "ProductId",
    ),
    LoadSpec(
        "product_product_suppliers.csv",
        "product",
        "ProductSupplier",
        (
            "ProductId",
            "SupplierId",
            "SupplierProductCode",
            "SupplierCost",
            "LeadTimeDays",
            "IsPrimarySupplier",
            "IsActive",
        ),
    ),

    LoadSpec(
        "customer_customers.csv",
        "customer",
        "Customer",
        (
            "CustomerId",
            "CustomerCode",
            "FirstName",
            "LastName",
            "Gender",
            "DateOfBirth",
            "Email",
            "Phone",
            "Nationality",
            "RegistrationDate",
            "PreferredEmirateId",
            "PreferredChannelId",
            "IsActive",
        ),
        "CustomerId",
    ),
    LoadSpec(
        "customer_segment_history.csv",
        "customer",
        "CustomerSegmentHistory",
        (
            "CustomerSegmentHistoryId",
            "CustomerId",
            "SegmentName",
            "EffectiveFrom",
            "EffectiveTo",
            "IsCurrent",
        ),
        "CustomerSegmentHistoryId",
    ),

    LoadSpec(
        "sales_promotions.csv",
        "sales",
        "Promotion",
        (
            "PromotionId",
            "PromotionCode",
            "PromotionName",
            "PromotionType",
            "DiscountType",
            "DiscountValue",
            "StartDate",
            "EndDate",
            "IsActive",
        ),
        "PromotionId",
    ),
    LoadSpec(
        "sales_promotion_products.csv",
        "sales",
        "PromotionProduct",
        (
            "PromotionId",
            "ProductId",
        ),
    ),
    LoadSpec(
        "sales_promotion_categories.csv",
        "sales",
        "PromotionCategory",
        (
            "PromotionId",
            "CategoryId",
        ),
    ),
    LoadSpec(
        "sales_promotion_stores.csv",
        "sales",
        "PromotionStore",
        (
            "PromotionId",
            "StoreId",
        ),
    ),

    LoadSpec(
        "sales_orders.csv",
        "sales",
        "SalesOrder",
        (
            "OrderId",
            "OrderNumber",
            "CustomerId",
            "StoreId",
            "SalesChannelId",
            "DateKey",
            "OrderDateTime",
            "OrderStatus",
            "GrossAmount",
            "DiscountAmount",
            "NetAmount",
            "VATAmount",
            "CustomerTotal",
        ),
        "OrderId",
        3000,
    ),
    LoadSpec(
        "sales_order_items.csv",
        "sales",
        "SalesOrderItem",
        (
            "OrderItemId",
            "OrderId",
            "ProductId",
            "PromotionId",
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
        ),
        "OrderItemId",
        3000,
    ),
    LoadSpec(
        "sales_order_payments.csv",
        "sales",
        "OrderPayment",
        (
            "OrderPaymentId",
            "OrderId",
            "PaymentMethodId",
            "PaymentAmount",
            "PaymentDateTime",
            "PaymentReference",
        ),
        "OrderPaymentId",
        3000,
    ),

    LoadSpec(
        "sales_returns.csv",
        "sales",
        "Return",
        (
            "ReturnId",
            "ReturnNumber",
            "OrderId",
            "StoreId",
            "DateKey",
            "ReturnDateTime",
            "ReturnStatus",
            "TotalReturnNetAmount",
            "TotalVATReversed",
            "TotalRefundAmount",
        ),
        "ReturnId",
    ),
    LoadSpec(
        "sales_return_items.csv",
        "sales",
        "ReturnItem",
        (
            "ReturnItemId",
            "ReturnId",
            "OrderItemId",
            "ReturnQuantity",
            "ReturnReason",
            "ReturnedNetAmount",
            "VATReversed",
            "RefundAmount",
            "IsRestockable",
        ),
        "ReturnItemId",
    ),
    LoadSpec(
        "sales_refunds.csv",
        "sales",
        "Refund",
        (
            "RefundId",
            "ReturnId",
            "PaymentMethodId",
            "RefundAmount",
            "RefundDateTime",
            "RefundReference",
            "RefundStatus",
        ),
        "RefundId",
    ),

    LoadSpec(
        "inventory_store_product.csv",
        "inventory",
        "StoreProductInventory",
        (
            "StoreId",
            "ProductId",
            "ReorderPoint",
            "ReorderQuantity",
            "CurrentStock",
            "LastUpdatedAt",
        ),
        batch_size=3000,
    ),
    LoadSpec(
        "inventory_movements.csv",
        "inventory",
        "InventoryMovement",
        (
            "InventoryMovementId",
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
        ),
        "InventoryMovementId",
        3000,
    ),

    LoadSpec(
        "sales_store_monthly_targets.csv",
        "sales",
        "StoreMonthlyTarget",
        (
            "StoreMonthlyTargetId",
            "StoreId",
            "TargetYear",
            "TargetMonth",
            "RevenueTarget",
            "GrossProfitTarget",
            "OrdersTarget",
        ),
        "StoreMonthlyTargetId",
    ),
)


def _table_count(
    connection: Connection,
    spec: LoadSpec,
) -> int:
    return int(
        connection.execute(
            text(
                f"""
                SELECT COUNT_BIG(*)
                FROM {spec.full_table_name}
                """
            )
        ).scalar_one()
    )


def validate_target_tables_empty(
    connection: Connection,
) -> None:
    nonempty = []

    for spec in LOAD_PLAN:
        count = _table_count(
            connection,
            spec,
        )

        if count:
            nonempty.append(
                (
                    spec.full_table_name,
                    count,
                )
            )

    if nonempty:
        detail = "; ".join(
            f"{table}={count:,}"
            for table, count
            in nonempty
        )

        raise RuntimeError(
            "Bulk load cancelled because "
            "target tables are not empty: "
            + detail
        )


def _load_csv(
    data_directory: Path,
    spec: LoadSpec,
) -> pd.DataFrame:
    path = (
        data_directory
        / spec.file_name
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    missing = (
        set(spec.columns)
        - set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            f"{spec.file_name} missing "
            "load columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    dataframe = dataframe[
        list(spec.columns)
    ].copy()

    # Convert Pandas NaN/NaT values into Python None so
    # pyodbc sends SQL NULL.
    dataframe = dataframe.astype(
        object
    ).where(
        pd.notna(dataframe),
        None,
    )

    return dataframe


def _insert_batch(
    connection: Connection,
    spec: LoadSpec,
    dataframe: pd.DataFrame,
) -> None:
    if dataframe.empty:
        return

    column_sql = ", ".join(
        f"[{column}]"
        for column in spec.columns
    )

    parameter_sql = ", ".join(
        f":{column}"
        for column in spec.columns
    )

    statement = text(
        f"""
        INSERT INTO {spec.full_table_name}
        (
            {column_sql}
        )
        VALUES
        (
            {parameter_sql}
        )
        """
    )

    total_rows = len(
        dataframe
    )

    for start in range(
        0,
        total_rows,
        spec.batch_size,
    ):
        end = min(
            start
            + spec.batch_size,
            total_rows,
        )

        batch = (
            dataframe.iloc[
                start:end
            ]
            .to_dict(
                orient="records"
            )
        )

        connection.execute(
            statement,
            batch,
        )


def load_table(
    connection: Connection,
    data_directory: Path,
    spec: LoadSpec,
) -> int:
    dataframe = _load_csv(
        data_directory,
        spec,
    )

    identity_enabled = False

    try:
        if (
            spec.identity_column
            is not None
        ):
            connection.execute(
                text(
                    f"""
                    SET IDENTITY_INSERT
                    {spec.full_table_name}
                    ON
                    """
                )
            )

            identity_enabled = True

        _insert_batch(
            connection,
            spec,
            dataframe,
        )

    finally:
        if identity_enabled:
            connection.execute(
                text(
                    f"""
                    SET IDENTITY_INSERT
                    {spec.full_table_name}
                    OFF
                    """
                )
            )

    database_count = _table_count(
        connection,
        spec,
    )

    if database_count != len(
        dataframe
    ):
        raise RuntimeError(
            f"Row count mismatch for "
            f"{spec.full_table_name}: "
            f"CSV={len(dataframe):,}, "
            f"SQL={database_count:,}"
        )

    return database_count


def bulk_load_all(
    engine: Engine,
    data_directory: Path,
) -> list[
    tuple[str, int]
]:
    loaded_tables = []

    # One transaction for the complete load.
    with engine.begin() as connection:
        validate_target_tables_empty(
            connection
        )

        for spec in LOAD_PLAN:
            count = load_table(
                connection=connection,
                data_directory=(
                    data_directory
                ),
                spec=spec,
            )

            loaded_tables.append(
                (
                    (
                        f"{spec.schema}."
                        f"{spec.table}"
                    ),
                    count,
                )
            )

            print(
                f"  "
                f"{spec.schema}.{spec.table:<30}"
                f"{count:>12,} rows"
            )

    return loaded_tables