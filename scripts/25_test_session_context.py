"""
UAE Retail Intelligence Platform
STEP 25 - SQL SESSION_CONTEXT Test

Tests:
- Application users exist.
- UserId can be assigned to SQL SESSION_CONTEXT.
- SQL Server sees the correct UserId.
- Context is isolated per application operation.
- Context is cleared before pooled connection reuse.
"""

from sqlalchemy import text

from src.database.connection import (
    get_engine,
)
from src.security.session_context import (
    get_session_user_id,
    user_database_connection,
)


TEST_USERS = [
    "ceo",
    "dubai.manager",
    "store.manager",
    "inventory.analyst",
]


def load_user_ids():
    engine = get_engine()

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

                    ORDER BY
                        UserId
                    """
                )
            )
            .mappings()
            .all()
        )

    return {
        row[
            "Username"
        ]:
            int(
                row[
                    "UserId"
                ]
            )
        for row in rows
    }


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 25 - SQL SESSION_CONTEXT TEST"
    )
    print("=" * 78)

    engine = get_engine()

    user_ids = (
        load_user_ids()
    )

    missing = (
        set(
            TEST_USERS
        )
        - set(
            user_ids
        )
    )

    if missing:
        raise RuntimeError(
            "Missing application users: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    failures = 0

    for username in (
        TEST_USERS
    ):
        expected_user_id = (
            user_ids[
                username
            ]
        )

        with user_database_connection(
            user_id=(
                expected_user_id
            ),
            engine=engine,
        ) as connection:

            actual_user_id = (
                get_session_user_id(
                    connection
                )
            )

            sql_username = (
                connection.execute(
                    text(
                        """
                        SELECT Username
                        FROM security.AppUser
                        WHERE
                            UserId
                            =
                            TRY_CONVERT(
                                INT,
                                SESSION_CONTEXT(
                                    N'UserId'
                                )
                            )
                        """
                    )
                ).scalar_one()
            )

            passed = (
                actual_user_id
                == expected_user_id
                and sql_username
                == username
            )

            if passed:
                print(
                    f"[PASS] "
                    f"{username:<20}"
                    f"UserId="
                    f"{actual_user_id}"
                )

            else:
                failures += 1

                print(
                    f"[FAIL] "
                    f"{username}"
                )

    # ========================================================
    # Pool leakage check
    # ========================================================

    with engine.connect() as connection:
        leaked_user_id = (
            get_session_user_id(
                connection
            )
        )

    if leaked_user_id is None:
        print(
            "[PASS] Pooled connection "
            "contains no leaked UserId"
        )
    else:
        failures += 1

        print(
            "[FAIL] SESSION_CONTEXT leak "
            f"detected: UserId="
            f"{leaked_user_id}"
        )

    # ========================================================
    # Sequential user isolation
    # ========================================================

    ceo_id = (
        user_ids[
            "ceo"
        ]
    )

    manager_id = (
        user_ids[
            "dubai.manager"
        ]
    )

    with user_database_connection(
        user_id=ceo_id,
        engine=engine,
    ) as connection:

        first = (
            get_session_user_id(
                connection
            )
        )

    with user_database_connection(
        user_id=manager_id,
        engine=engine,
    ) as connection:

        second = (
            get_session_user_id(
                connection
            )
        )

    if (
        first == ceo_id
        and second == manager_id
    ):
        print(
            "[PASS] Sequential users "
            "receive isolated contexts"
        )

    else:
        failures += 1

        print(
            "[FAIL] Sequential context "
            "isolation"
        )

    print("-" * 78)

    if failures:
        print(
            f"Failed checks: "
            f"{failures}"
        )

        print(
            "SESSION_CONTEXT TEST: FAILED"
        )

        print("=" * 78)

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "SESSION_CONTEXT TEST: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()