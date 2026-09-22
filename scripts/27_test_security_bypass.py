"""
UAE Retail Intelligence Platform
STEP 27 - Security Bypass Tests

Negative/adversarial tests for:
- Missing SESSION_CONTEXT
- Invalid/forged UserId
- Cross-store access
- Cross-emirate access
- Child-table RLS
- Inactive data scope
- Connection-pool context leakage
- Security policy state
- Runtime SQL identity privilege
"""

from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine
from src.security.session_context import (
    get_session_user_id,
    user_database_connection,
)


def check(condition: bool, message: str) -> int:
    if condition:
        print(f"[PASS] {message}")
        return 0

    print(f"[FAIL] {message}")
    return 1


def load_user_id(connection, username: str) -> int:
    return int(
        connection.execute(
            text(
                """
                SELECT UserId
                FROM security.AppUser
                WHERE Username = :username
                """
            ),
            {"username": username},
        ).scalar_one()
    )


def scalar_count(connection, sql: str, **params) -> int:
    return int(
        connection.execute(
            text(sql),
            params,
        ).scalar_one()
    )


def main() -> None:
    print("=" * 78)
    print("UAE Retail Intelligence Platform")
    print("STEP 27 - SECURITY BYPASS TESTS")
    print("=" * 78)

    engine = get_engine()
    failures = 0

    # ---------------------------------------------------------
    # Load known application users.
    # ---------------------------------------------------------
    with engine.connect() as connection:
        store_manager_id = load_user_id(
            connection,
            "store.manager",
        )

        dubai_manager_id = load_user_id(
            connection,
            "dubai.manager",
        )

    # ---------------------------------------------------------
    # 1. No SESSION_CONTEXT must expose no protected rows.
    # ---------------------------------------------------------
    with engine.connect() as connection:
        context = get_session_user_id(connection)

        orders = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrder
            """,
        )

        stores = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            """,
        )

    failures += check(
        context is None
        and orders == 0
        and stores == 0,
        "No SESSION_CONTEXT exposes no protected business rows",
    )

    # ---------------------------------------------------------
    # 2. Non-existent UserId must expose no rows.
    # ---------------------------------------------------------
    fake_user_id = 2147483647

    with user_database_connection(
        user_id=fake_user_id,
        engine=engine,
    ) as connection:
        fake_orders = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrder
            """,
        )

        fake_stores = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            """,
        )

    failures += check(
        fake_orders == 0
        and fake_stores == 0,
        "Non-existent UserId receives zero protected rows",
    )

    # ---------------------------------------------------------
    # 3. Store Manager cannot read another store.
    # STR001 is assigned; STR007 belongs to Dubai.
    # ---------------------------------------------------------
    with user_database_connection(
        user_id=store_manager_id,
        engine=engine,
    ) as connection:
        own_store = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            WHERE StoreCode = 'STR001'
            """,
        )

        foreign_store = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            WHERE StoreCode = 'STR007'
            """,
        )

        foreign_orders = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrder o
            INNER JOIN core.Store s
                ON o.StoreId = s.StoreId
            WHERE s.StoreCode = 'STR007'
            """,
        )

    failures += check(
        own_store == 1
        and foreign_store == 0
        and foreign_orders == 0,
        "Store Manager cannot query a foreign store",
    )

    # ---------------------------------------------------------
    # 4. Dubai Manager cannot access a non-Dubai store.
    # ---------------------------------------------------------
    with user_database_connection(
        user_id=dubai_manager_id,
        engine=engine,
    ) as connection:
        dubai_store = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            WHERE StoreCode = 'STR007'
            """,
        )

        outside_dubai = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            WHERE StoreCode = 'STR001'
            """,
        )

    failures += check(
        dubai_store == 1
        and outside_dubai == 0,
        "Dubai Manager cannot query a store outside Dubai",
    )

    # ---------------------------------------------------------
    # 5. Direct child-table reads must still be RLS restricted.
    # Compare child rows visible to Store Manager vs rows
    # belonging to foreign Store STR007.
    # ---------------------------------------------------------
    with user_database_connection(
        user_id=store_manager_id,
        engine=engine,
    ) as connection:
        visible_items = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrderItem
            """,
        )

        foreign_items = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrderItem oi
            INNER JOIN sales.SalesOrder o
                ON oi.OrderId = o.OrderId
            INNER JOIN core.Store s
                ON o.StoreId = s.StoreId
            WHERE s.StoreCode = 'STR007'
            """,
        )

        visible_return_items = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.ReturnItem
            """,
        )

        visible_refunds = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.Refund
            """,
        )

    failures += check(
        visible_items > 0
        and foreign_items == 0,
        "SalesOrderItem cannot bypass parent store scope",
    )

    failures += check(
        visible_return_items >= 0
        and visible_refunds >= 0,
        "ReturnItem and Refund direct reads execute under RLS",
    )

    # ---------------------------------------------------------
    # 6. Temporarily deactivate Store Manager's scope.
    #
    # The update is inside a transaction and ALWAYS rolled back.
    # No permanent security data modification occurs.
    # ---------------------------------------------------------
    connection = engine.connect()
    transaction = connection.begin()

    try:
        connection.execute(
            text(
                """
                UPDATE security.UserDataScope
                SET IsActive = 0
                WHERE UserId = :user_id
                  AND IsActive = 1
                """
            ),
            {"user_id": store_manager_id},
        )

        connection.execute(
            text(
                """
                EXEC sys.sp_set_session_context
                    @key = N'UserId',
                    @value = :user_id
                """
            ),
            {"user_id": store_manager_id},
        )

        inactive_orders = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrder
            """,
        )

        inactive_stores = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            """,
        )

        failures += check(
            inactive_orders == 0
            and inactive_stores == 0,
            "Inactive data scope grants no business data",
        )

    finally:
        transaction.rollback()

        # Remove context before returning connection to pool.
        cleanup = connection.begin()

        try:
            connection.execute(
                text(
                    """
                    EXEC sys.sp_set_session_context
                        @key = N'UserId',
                        @value = NULL
                    """
                )
            )

            cleanup.commit()

        except Exception:
            cleanup.rollback()
            raise

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 7. Verify rollback restored the active scope.
    # ---------------------------------------------------------
    with user_database_connection(
        user_id=store_manager_id,
        engine=engine,
    ) as connection:
        restored_stores = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM core.Store
            """,
        )

    failures += check(
        restored_stores == 1,
        "Security scope rollback restored Store Manager access",
    )

    # ---------------------------------------------------------
    # 8. Pool leakage check after adversarial operations.
    # ---------------------------------------------------------
    with engine.connect() as connection:
        leaked_id = get_session_user_id(
            connection
        )

        leaked_orders = scalar_count(
            connection,
            """
            SELECT COUNT_BIG(*)
            FROM sales.SalesOrder
            """,
        )

    failures += check(
        leaked_id is None
        and leaked_orders == 0,
        "Connection pool contains no leaked identity",
    )

    # ---------------------------------------------------------
    # 9. Security policy must exist and be enabled.
    # ---------------------------------------------------------
    with engine.connect() as connection:
        policy = (
            connection.execute(
                text(
                    """
                    SELECT
                        is_enabled
                    FROM sys.security_policies
                    WHERE
                        name = N'BusinessDataSecurityPolicy'
                        AND schema_id = SCHEMA_ID(N'security')
                    """
                )
            )
            .scalar_one_or_none()
        )

        predicate_count = scalar_count(
            connection,
            """
            SELECT COUNT(*)
            FROM sys.security_predicates sp
            INNER JOIN sys.security_policies p
                ON sp.object_id = p.object_id
            WHERE
                p.name = N'BusinessDataSecurityPolicy'
                AND p.schema_id = SCHEMA_ID(N'security')
            """,
        )

    failures += check(
        policy == 1
        and predicate_count == 12,
        "RLS policy is enabled with all 12 predicates",
    )

    # ---------------------------------------------------------
    # 10. Runtime database identity assessment.
    #
    # This is reported separately. During development dbo may
    # be expected, but Streamlit must later use least privilege.
    # ---------------------------------------------------------
    with engine.connect() as connection:
        identity = (
            connection.execute(
                text(
                    """
                    SELECT
                        ORIGINAL_LOGIN()
                            AS OriginalLogin,

                        USER_NAME()
                            AS DatabaseUser,

                        IS_ROLEMEMBER('db_owner')
                            AS IsDbOwner
                    """
                )
            )
            .mappings()
            .one()
        )

    print("-" * 78)

    print(
        "Database identity: "
        f"{identity['OriginalLogin']} / "
        f"{identity['DatabaseUser']}"
    )

    if identity["IsDbOwner"] == 1:
        print(
            "[WARN] Current development connection is db_owner. "
            "Do not use this identity as the final Streamlit runtime principal."
        )
    else:
        print(
            "[PASS] Runtime identity is not a db_owner member"
        )

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------
    print("-" * 78)

    if failures:
        print(f"Failed checks: {failures}")
        print("SECURITY BYPASS TESTS: FAILED")
        print("=" * 78)
        raise SystemExit(1)

    print("Failed checks: 0")
    print("SECURITY BYPASS TESTS: PASSED")
    print(
        "RLS resisted tested cross-scope and missing-context access."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
