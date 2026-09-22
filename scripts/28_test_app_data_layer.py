"""
STEP 28 - Application Data Layer Test
"""

from sqlalchemy import text

from src.analytics.app_data import (
    PermissionDeniedError,
    get_executive_summary,
    get_inventory_status,
    get_store_performance,
    get_visible_stores,
)
from src.database.connection import get_engine
from src.security.authentication import AuthenticatedUser


def load_user(
    username: str,
) -> AuthenticatedUser:
    engine = get_engine()

    with engine.connect() as connection:
        row = (
            connection.execute(
                text("""
                    SELECT UserId, Username, Email
                    FROM security.AppUser
                    WHERE Username = :username
                """),
                {"username": username},
            )
            .mappings()
            .one()
        )

        roles = set(
            connection.execute(
                text("""
                    SELECT r.RoleName
                    FROM security.UserRole ur
                    INNER JOIN security.Role r
                        ON ur.RoleId = r.RoleId
                    WHERE ur.UserId = :user_id
                """),
                {"user_id": row["UserId"]},
            ).scalars()
        )

        permissions = set(
            connection.execute(
                text("""
                    SELECT DISTINCT p.PermissionCode
                    FROM security.UserRole ur
                    INNER JOIN security.RolePermission rp
                        ON ur.RoleId = rp.RoleId
                    INNER JOIN security.Permission p
                        ON rp.PermissionId = p.PermissionId
                    WHERE ur.UserId = :user_id
                """),
                {"user_id": row["UserId"]},
            ).scalars()
        )

    return AuthenticatedUser(
        user_id=int(row["UserId"]),
        username=str(row["Username"]),
        email=str(row["Email"]),
        roles=roles,
        permissions=permissions,
        scopes=[],
    )


def check(
    condition: bool,
    message: str,
) -> int:
    if condition:
        print(f"[PASS] {message}")
        return 0

    print(f"[FAIL] {message}")
    return 1


def main():
    print("=" * 78)
    print("STEP 28 - APPLICATION DATA LAYER TEST")
    print("=" * 78)

    failures = 0

    ceo = load_user("ceo")
    dubai = load_user("dubai.manager")
    store = load_user("store.manager")
    inventory = load_user(
        "inventory.analyst"
    )

    ceo_stores = get_visible_stores(ceo)
    dubai_stores = get_visible_stores(dubai)
    store_stores = get_visible_stores(store)

    failures += check(
        len(ceo_stores) == 25,
        "CEO data layer sees 25 stores",
    )

    failures += check(
        len(dubai_stores) == 7
        and set(
            dubai_stores["EmirateName"]
        ) == {"Dubai"},
        "Dubai Manager data layer sees Dubai only",
    )

    failures += check(
        len(store_stores) == 1
        and store_stores.iloc[0]["StoreCode"]
        == "STR001",
        "Store Manager data layer sees STR001 only",
    )

    stores = get_store_performance(store)

    failures += check(
        len(stores) == 1
        and stores.iloc[0]["StoreCode"]
        == "STR001",
        "Store analytics respects RLS",
    )

    summary = get_executive_summary(ceo)

    failures += check(
        float(summary["Revenue"]) > 0,
        "CEO executive summary returns data",
    )

    inventory_data = get_inventory_status(
        inventory
    )

    failures += check(
        not inventory_data.empty,
        "Inventory Analyst can access inventory",
    )

    try:
        get_executive_summary(inventory)

        failures += 1
        print(
            "[FAIL] Unauthorized executive access accepted"
        )

    except PermissionDeniedError:
        print(
            "[PASS] Unauthorized executive access rejected"
        )

    print("-" * 78)

    if failures:
        print(f"Failed checks: {failures}")
        print(
            "APPLICATION DATA LAYER TEST: FAILED"
        )
        raise SystemExit(1)

    print("Failed checks: 0")
    print(
        "APPLICATION DATA LAYER TEST: PASSED"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
