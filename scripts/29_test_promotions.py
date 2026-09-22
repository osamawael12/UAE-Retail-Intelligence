"""
UAE Retail Intelligence Platform
STEP 29 - Secure Promotion Analytics Test

Validates:
- promotion data layer returns data
- CEO receives company-wide promoted data
- Dubai Manager remains Dubai scoped
- Store Manager remains STR001 scoped
- user without VIEW_SALES cannot access promotion analytics
- promotion calculations are internally consistent
"""

from __future__ import annotations

from sqlalchemy import text

from src.analytics.promotion_data import (
    PromotionPermissionError,
    get_campaign_performance,
    get_promotion_emirate_performance,
    get_promotion_kpis,
    get_promotion_status_summary,
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

                    WHERE
                        Username = :username
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
                    SELECT
                        r.RoleName

                    FROM security.UserRole ur

                    INNER JOIN security.Role r
                        ON ur.RoleId
                           = r.RoleId

                    WHERE
                        ur.UserId
                        = :user_id
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

                    INNER JOIN
                        security.RolePermission rp
                        ON ur.RoleId
                           = rp.RoleId

                    INNER JOIN security.Permission p
                        ON rp.PermissionId
                           = p.PermissionId

                    WHERE
                        ur.UserId
                        = :user_id
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


def main() -> None:
    print("=" * 78)
    print(
        "STEP 29 - SECURE "
        "PROMOTION ANALYTICS TEST"
    )
    print("=" * 78)

    failures = 0

    ceo = load_user(
        "ceo"
    )

    dubai = load_user(
        "dubai.manager"
    )

    store = load_user(
        "store.manager"
    )

    inventory = load_user(
        "inventory.analyst"
    )

    ceo_kpis = (
        get_promotion_kpis(
            ceo
        )
    )

    failures += check(
        ceo_kpis[
            "SalesLines"
        ] > 0
        and ceo_kpis[
            "PromotedSalesLines"
        ] > 0,
        (
            "CEO promotion analytics "
            "returns promoted sales"
        ),
    )

    campaigns = (
        get_campaign_performance(
            ceo
        )
    )

    failures += check(
        not campaigns.empty
        and campaigns[
            "PromotionId"
        ].nunique()
        > 0,
        (
            "Campaign performance "
            "returns campaigns"
        ),
    )

    status = (
        get_promotion_status_summary(
            ceo
        )
    )

    status_set = set(
        status[
            "PromotionStatus"
        ]
    )

    failures += check(
        "Promoted"
        in status_set
        and "Non-Promoted"
        in status_set,
        (
            "Promoted and non-promoted "
            "sales are both available"
        ),
    )

    dubai_geo = (
        get_promotion_emirate_performance(
            dubai
        )
    )

    failures += check(
        not dubai_geo.empty
        and set(
            dubai_geo[
                "EmirateName"
            ]
        )
        == {"Dubai"},
        (
            "Dubai Manager promotion "
            "analytics remains Dubai scoped"
        ),
    )

    store_geo = (
        get_promotion_emirate_performance(
            store
        )
    )

    failures += check(
        not store_geo.empty
        and set(
            store_geo[
                "EmirateName"
            ]
        )
        == {"Abu Dhabi"},
        (
            "Store Manager promotion "
            "analytics remains store scoped"
        ),
    )

    try:
        get_promotion_kpis(
            inventory
        )

        failures += 1

        print(
            "[FAIL] Inventory Analyst "
            "accessed sales promotion analytics"
        )

    except PromotionPermissionError:
        print(
            "[PASS] Inventory Analyst "
            "sales promotion access rejected"
        )

    adoption = float(
        ceo_kpis[
            "PromotionLineAdoptionPct"
        ]
    )

    failures += check(
        0 <= adoption <= 100,
        (
            "Promotion adoption rate "
            "is within valid bounds"
        ),
    )

    promoted_share = float(
        ceo_kpis[
            "PromotedRevenueSharePct"
        ]
    )

    failures += check(
        0 <= promoted_share <= 100,
        (
            "Promoted revenue share "
            "is within valid bounds"
        ),
    )

    print("-" * 78)

    if failures:
        print(
            f"Failed checks: "
            f"{failures}"
        )

        print(
            "PROMOTION ANALYTICS "
            "TEST: FAILED"
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "PROMOTION ANALYTICS "
        "TEST: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()