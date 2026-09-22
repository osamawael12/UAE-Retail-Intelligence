"""
UAE Retail Intelligence Platform
STEP 26 - SQL Server RLS Security Test

Demonstrates:

CEO
→ all 25 stores / 7 emirates

Dubai Manager
→ Dubai stores only

Store Manager
→ one store only

Inventory Analyst
→ all stores due to ALL data scope

Most importantly:
Queries intentionally contain NO application WHERE clause
limiting the user to their scope.

SQL Server RLS performs the restriction.
"""

from __future__ import annotations

from sqlalchemy import text

from src.database.connection import (
    get_engine,
)
from src.security.session_context import (
    user_database_connection,
)


USERS = [
    "ceo",
    "dubai.manager",
    "store.manager",
    "inventory.analyst",
]


def load_users(
    engine,
) -> dict:
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        UserId,
                        Username
                    FROM security.AppUser
                    WHERE
                        Username IN
                        (
                            'ceo',
                            'dubai.manager',
                            'store.manager',
                            'inventory.analyst'
                        )
                    """
                )
            )
            .mappings()
            .all()
        )

    return {
        row["Username"]:
            int(
                row["UserId"]
            )
        for row in rows
    }


def query_scope(
    connection,
) -> dict:
    """
    NO user-specific WHERE filters are used.
    """

    result = (
        connection.execute(
            text(
                """
                SELECT
                    COUNT(
                        DISTINCT e.EmirateId
                    ) AS Emirates,

                    COUNT(
                        DISTINCT s.StoreId
                    ) AS Stores,

                    COUNT_BIG(
                        DISTINCT o.OrderId
                    ) AS Orders,

                    COUNT_BIG(
                        DISTINCT o.CustomerId
                    ) AS Customers,

                    CAST(
                        SUM(i.NetAmount)
                        -
                        COALESCE(
                            SUM(
                                ri.ReturnedNetAmount
                            ),
                            0
                        )
                        AS DECIMAL(19,2)
                    ) AS ApproxRevenue

                FROM sales.SalesOrder o

                INNER JOIN
                    sales.SalesOrderItem i
                    ON o.OrderId
                       = i.OrderId

                INNER JOIN core.Store s
                    ON o.StoreId
                       = s.StoreId

                INNER JOIN core.City c
                    ON s.CityId
                       = c.CityId

                INNER JOIN core.Emirate e
                    ON c.EmirateId
                       = e.EmirateId

                LEFT JOIN sales.ReturnItem ri
                    ON i.OrderItemId
                       = ri.OrderItemId

                WHERE
                    o.OrderStatus
                    = 'COMPLETED'
                """
            )
        )
        .mappings()
        .one()
    )

    return dict(
        result
    )


def visible_store_codes(
    connection,
) -> list[str]:
    return list(
        connection.execute(
            text(
                """
                SELECT
                    StoreCode
                FROM core.Store
                ORDER BY StoreCode
                """
            )
        ).scalars()
    )


def visible_emirates(
    connection,
) -> list[str]:
    return list(
        connection.execute(
            text(
                """
                SELECT DISTINCT
                    e.EmirateName

                FROM core.Store s

                INNER JOIN core.City c
                    ON s.CityId
                       = c.CityId

                INNER JOIN core.Emirate e
                    ON c.EmirateId
                       = e.EmirateId

                ORDER BY
                    e.EmirateName
                """
            )
        ).scalars()
    )


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 26 - SQL SERVER RLS TEST"
    )
    print("=" * 78)

    engine = get_engine()

    users = load_users(
        engine
    )

    failures = 0

    results = {}

    for username in USERS:
        user_id = users[
            username
        ]

        with user_database_connection(
            user_id=user_id,
            engine=engine,
        ) as connection:

            scope = query_scope(
                connection
            )

            stores = (
                visible_store_codes(
                    connection
                )
            )

            emirates = (
                visible_emirates(
                    connection
                )
            )

            results[
                username
            ] = {
                "scope":
                    scope,

                "stores":
                    stores,

                "emirates":
                    emirates,
            }

        print(
            f"\n{username}"
        )

        print(
            f"  Emirates : "
            f"{scope['Emirates']}"
        )

        print(
            f"  Stores   : "
            f"{scope['Stores']}"
        )

        print(
            f"  Orders   : "
            f"{scope['Orders']:,}"
        )

        print(
            f"  Customers: "
            f"{scope['Customers']:,}"
        )

        print(
            f"  Revenue  : "
            f"AED "
            f"{float(scope['ApproxRevenue'] or 0):,.2f}"
        )

        print(
            "  Visible Emirates: "
            + ", ".join(
                emirates
            )
        )

        print(
            "  Visible Stores: "
            + ", ".join(
                stores
            )
        )

    # ========================================================
    # CEO
    # ========================================================

    ceo = results[
        "ceo"
    ]

    if (
        ceo[
            "scope"
        ][
            "Stores"
        ]
        == 25
        and ceo[
            "scope"
        ][
            "Emirates"
        ]
        == 7
    ):
        print(
            "\n[PASS] CEO sees all UAE stores"
        )
    else:
        failures += 1

        print(
            "\n[FAIL] CEO scope"
        )

    # ========================================================
    # Dubai Manager
    # ========================================================

    dubai = results[
        "dubai.manager"
    ]

    if (
        dubai[
            "scope"
        ][
            "Stores"
        ]
        == 7
        and dubai[
            "emirates"
        ]
        == [
            "Dubai"
        ]
    ):
        print(
            "[PASS] Dubai Manager sees Dubai only"
        )
    else:
        failures += 1

        print(
            "[FAIL] Dubai Manager scope"
        )

    # ========================================================
    # Store Manager
    # ========================================================

    store_manager = (
        results[
            "store.manager"
        ]
    )

    if (
        store_manager[
            "scope"
        ][
            "Stores"
        ]
        == 1
        and store_manager[
            "stores"
        ]
        == [
            "STR001"
        ]
    ):
        print(
            "[PASS] Store Manager sees STR001 only"
        )
    else:
        failures += 1

        print(
            "[FAIL] Store Manager scope"
        )

    # ========================================================
    # Inventory Analyst
    # ========================================================

    inventory = (
        results[
            "inventory.analyst"
        ]
    )

    if (
        inventory[
            "scope"
        ][
            "Stores"
        ]
        == 25
    ):
        print(
            "[PASS] Inventory Analyst ALL scope"
        )
    else:
        failures += 1

        print(
            "[FAIL] Inventory Analyst scope"
        )

    # ========================================================
    # NO CONTEXT
    # ========================================================

    with engine.connect() as connection:
        count_without_context = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT_BIG(*)
                    FROM sales.SalesOrder
                    """
                )
            ).scalar_one()
        )

    if count_without_context == 0:
        print(
            "[PASS] No SESSION_CONTEXT returns no orders"
        )
    else:
        failures += 1

        print(
            "[FAIL] No-context query exposed "
            f"{count_without_context:,} orders"
        )

    print("-" * 78)

    if failures:
        print(
            f"Failed checks: "
            f"{failures}"
        )

        print(
            "RLS TEST: FAILED"
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "RLS TEST: PASSED"
    )

    print(
        "SQL Server is enforcing data scope."
    )

    print("=" * 78)


if __name__ == "__main__":
    main()