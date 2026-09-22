from sqlalchemy import inspect

from src.database.connection import get_engine


EXPECTED_TABLES = {
    "core": {
        "Emirate",
        "City",
        "Store",
        "DateDimension",
        "SalesChannel",
        "PaymentMethod",
        "Employee",
    },
    "product": {
        "Category",
        "Subcategory",
        "Brand",
        "Supplier",
        "Product",
        "ProductSupplier",
    },
    "customer": {
        "Customer",
        "CustomerSegmentHistory",
    },
    "sales": {
        "Promotion",
        "PromotionProduct",
        "PromotionCategory",
        "PromotionStore",
        "SalesOrder",
        "SalesOrderItem",
        "OrderPayment",
        "Return",
        "ReturnItem",
        "Refund",
        "StoreMonthlyTarget",
    },
    "inventory": {
        "StoreProductInventory",
        "InventoryMovement",
    },
    "security": {
        "AppUser",
        "Role",
        "Permission",
        "UserRole",
        "RolePermission",
        "UserDataScope",
        "AuditLog",
    },
}


def main():
    engine = get_engine()
    inspector = inspect(engine)

    has_errors = False
    total_expected = 0

    print("=" * 65)
    print("UAE Retail Intelligence - Database Schema Validation")
    print("=" * 65)

    for schema, expected_tables in EXPECTED_TABLES.items():

        actual_tables = set(
            inspector.get_table_names(schema=schema)
        )

        total_expected += len(expected_tables)

        missing = expected_tables - actual_tables
        unexpected = actual_tables - expected_tables

        print(f"\n[{schema}]")
        print(f"Expected : {len(expected_tables)}")
        print(f"Actual   : {len(actual_tables)}")

        if missing:
            has_errors = True
            print(
                "Missing  : "
                + ", ".join(sorted(missing))
            )
        else:
            print("Missing  : None")

        if unexpected:
            print(
                "Extra    : "
                + ", ".join(sorted(unexpected))
            )
        else:
            print("Extra    : None")

    print("\n" + "=" * 65)
    print(f"Expected application tables: {total_expected}")

    if has_errors:
        print("SCHEMA VALIDATION FAILED")
        raise SystemExit(1)

    print("SCHEMA VALIDATION PASSED")
    print("=" * 65)


if __name__ == "__main__":
    main()