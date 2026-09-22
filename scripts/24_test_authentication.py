"""
UAE Retail Intelligence Platform
Authentication / RBAC Smoke Test

Passwords are read from .env.
No password is printed.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.security.authentication import (
    authenticate,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT
    / ".env"
)


TEST_USERS = [
    (
        "ceo",
        "DEMO_CEO_PASSWORD",
    ),
    (
        "dubai.manager",
        "DEMO_DUBAI_MANAGER_PASSWORD",
    ),
    (
        "store.manager",
        "DEMO_STORE_MANAGER_PASSWORD",
    ),
    (
        "inventory.analyst",
        "DEMO_INVENTORY_PASSWORD",
    ),
]


def main() -> None:
    print("=" * 78)
    print(
        "AUTHENTICATION & RBAC TEST"
    )
    print("=" * 78)

    failures = 0

    for (
        username,
        env_name,
    ) in TEST_USERS:
        password = os.getenv(
            env_name
        )

        if not password:
            raise RuntimeError(
                f"Missing {env_name}"
            )

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            failures += 1

            print(
                f"[FAIL] {username}"
            )

            continue

        print(
            f"[PASS] {username}"
        )

        print(
            "       Roles: "
            + ", ".join(
                sorted(
                    user.roles
                )
            )
        )

        print(
            "       Permissions: "
            + ", ".join(
                sorted(
                    user.permissions
                )
            )
        )

        print(
            f"       Scopes: "
            f"{user.scopes}"
        )

    # Invalid password must fail.
    invalid = authenticate(
        username="ceo",
        password=(
            "DefinitelyWrongPassword!"
        ),
    )

    if invalid is None:
        print(
            "[PASS] Invalid password rejected"
        )
    else:
        failures += 1

        print(
            "[FAIL] Invalid password accepted"
        )

    print("-" * 78)

    if failures:
        print(
            f"Failed checks: "
            f"{failures}"
        )

        print(
            "AUTHENTICATION TEST: FAILED"
        )

        raise SystemExit(1)

    print(
        "Failed checks: 0"
    )

    print(
        "AUTHENTICATION TEST: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()