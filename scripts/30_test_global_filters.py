"""
UAE Retail Intelligence Platform
STEP 30 - Functional Global Filter Test

Validates:
- date filters narrow data
- emirate filters narrow data
- store filters narrow data
- filters cannot bypass SQL Server RLS
- filtered summaries are consistent
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text

from app.filters import (
    DashboardFilters,
)
from src.analytics.filtered_data import (
    get_filtered_emirate_performance,
    get_filtered_store_performance,
    get_filtered_summary,
)
from src.database.connection import (
    get_engine,
)
from src.security.authentication import (
    AuthenticatedUser,
)


def load_user(
    username: str,
) -> AuthenticatedUser:
    engine = get_engine()

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        UserId,
                        Username,
                        Email
                    FROM security.AppUser
                    WHERE Username = :username
                    """
                ),
                {
                    "username":
                        username
                },
            )
            .mappings()
            .one()
        )

        roles = set(
            connection.execute(
                text(
                    """
                    SELECT r.RoleName
                    FROM security.UserRole ur
                    INNER JOIN security.Role r
                        ON ur.RoleId = r.RoleId
                    WHERE ur.UserId = :user_id
                    """
                ),
                {
                    "user_id":
                        row["UserId"]
                },
            ).scalars()
        )

        permissions = set(
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        p.PermissionCode
                    FROM security.UserRole ur
                    INNER JOIN security.RolePermission rp
                        ON ur.RoleId = rp.RoleId
                    INNER JOIN security.Permission p
                        ON rp.PermissionId = p.PermissionId
                    WHERE ur.UserId = :user_id
                    """
                ),
                {
                    "user_id":
                        row["UserId"]
                },
            ).scalars()
        )

    return AuthenticatedUser(
        user_id=int(
            row["UserId"]
        ),
        username=str(
            row["Username"]
        ),
        email=str(
            row["Email"]
        ),
        roles=roles,
        permissions=permissions,
        scopes=[],
    )


def check(
    condition: bool,
    message: str,
) -> int:
    if condition:
        print(
            f"[PASS] {message}"
        )
        return 0

    print(
        f"[FAIL] {message}"
    )
    return 1


def filters(
    start=None,
    end=None,
    emirates=(),
    stores=(),
):
    return DashboardFilters(
        start_date=start,
        end_date=end,
        emirates=tuple(
            emirates
        ),
        store_ids=tuple(
            stores
        ),
    )


def main() -> None:
    print("=" * 78)
    print(
        "STEP 30 - FUNCTIONAL "
        "GLOBAL FILTER TEST"
    )
    print("=" * 78)

    failures = 0

    ceo = load_user(
        "ceo"
    )

    dubai = load_user(
        "dubai.manager"
    )

    store_manager = load_user(
        "store.manager"
    )

    all_filter = filters()

    full = get_filtered_summary(
        ceo,
        all_filter,
    )

    failures += check(
        float(
            full["Revenue"]
            or 0
        ) > 0,
        "Unfiltered CEO summary returns data",
    )

    year_filter = filters(
        start=date(
            2025,
            1,
            1,
        ),
        end=date(
            2025,
            12,
            31,
        ),
    )

    year_summary = (
        get_filtered_summary(
            ceo,
            year_filter,
        )
    )

    failures += check(
        0
        < float(
            year_summary[
                "Revenue"
            ]
            or 0
        )
        < float(
            full[
                "Revenue"
            ]
            or 0
        ),
        "Date filter narrows CEO revenue",
    )

    dubai_filter = filters(
        emirates=[
            "Dubai"
        ]
    )

    dubai_stores = (
        get_filtered_store_performance(
            ceo,
            dubai_filter,
        )
    )

    failures += check(
        len(
            dubai_stores
        ) == 7
        and set(
            dubai_stores[
                "EmirateName"
            ]
        )
        == {"Dubai"},
        "CEO Dubai filter returns Dubai only",
    )

    ceo_store_filter = filters(
        stores=[1]
    )

    ceo_store_data = (
        get_filtered_store_performance(
            ceo,
            ceo_store_filter,
        )
    )

    failures += check(
        len(
            ceo_store_data
        ) == 1
        and ceo_store_data.iloc[
            0
        ][
            "StoreCode"
        ]
        == "STR001",
        "Store filter returns STR001 only",
    )

    malicious_dubai_request = (
        filters(
            emirates=[
                "Abu Dhabi"
            ]
        )
    )

    dubai_attempt = (
        get_filtered_store_performance(
            dubai,
            malicious_dubai_request,
        )
    )

    failures += check(
        dubai_attempt.empty,
        (
            "Dubai Manager cannot use filter "
            "to access Abu Dhabi"
        ),
    )

    malicious_store_request = (
        filters(
            stores=[7]
        )
    )

    store_attempt = (
        get_filtered_store_performance(
            store_manager,
            malicious_store_request,
        )
    )

    failures += check(
        store_attempt.empty,
        (
            "Store Manager cannot use filter "
            "to access STR007"
        ),
    )

    store_own = (
        get_filtered_store_performance(
            store_manager,
            filters(
                stores=[1]
            ),
        )
    )

    failures += check(
        len(store_own) == 1
        and store_own.iloc[
            0
        ][
            "StoreCode"
        ]
        == "STR001",
        (
            "Store Manager can filter "
            "their own STR001"
        ),
    )

    dubai_geo = (
        get_filtered_emirate_performance(
            dubai,
            all_filter,
        )
    )

    failures += check(
        set(
            dubai_geo[
                "EmirateName"
            ]
        )
        == {"Dubai"},
        (
            "No analytical filter does not "
            "weaken Dubai RLS"
        ),
    )

    print("-" * 78)

    if failures:
        print(
            f"Failed checks: {failures}"
        )

        print(
            "GLOBAL FILTER TEST: FAILED"
        )

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "GLOBAL FILTER TEST: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()