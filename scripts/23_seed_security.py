"""
UAE Retail Intelligence Platform
STEP 23 - Security Seed

Creates:
- Roles
- Permissions
- RolePermission mappings
- Demo application users
- UserRole mappings
- UserDataScope mappings

Passwords are read from .env and stored only as Argon2 hashes.

The script refuses to run if application security data
already exists.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

from src.database.connection import (
    get_engine,
)
from src.security.passwords import (
    hash_password,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT
    / ".env"
)


ROLES = [
    (
        "CEO",
        "Company-wide executive analytics",
    ),
    (
        "Emirate Manager",
        "Management access within an assigned emirate",
    ),
    (
        "Store Manager",
        "Management access within an assigned store",
    ),
    (
        "Sales Analyst",
        "Commercial and sales analytics",
    ),
    (
        "Inventory Analyst",
        "Inventory and operational analytics",
    ),
    (
        "Admin",
        "Application user and permission administration",
    ),
]


PERMISSIONS = [
    (
        "VIEW_EXECUTIVE",
        "View Executive Analytics",
    ),
    (
        "VIEW_SALES",
        "View Sales Analytics",
    ),
    (
        "VIEW_STORES",
        "View Store Analytics",
    ),
    (
        "VIEW_PRODUCTS",
        "View Product Analytics",
    ),
    (
        "VIEW_CUSTOMERS",
        "View Customer Analytics",
    ),
    (
        "VIEW_RFM",
        "View RFM Analytics",
    ),
    (
        "VIEW_COHORTS",
        "View Cohort Analytics",
    ),
    (
        "VIEW_RETURNS",
        "View Returns Analytics",
    ),
    (
        "VIEW_INVENTORY",
        "View Inventory Analytics",
    ),
    (
        "VIEW_TARGETS",
        "View Target Analytics",
    ),
    (
        "VIEW_FORECAST",
        "View Forecast Analytics",
    ),
    (
        "EXPORT_DATA",
        "Export authorized analytical data",
    ),
    (
        "MANAGE_USERS",
        "Manage application users",
    ),
]


ROLE_PERMISSIONS = {
    "CEO": {
        "VIEW_EXECUTIVE",
        "VIEW_SALES",
        "VIEW_STORES",
        "VIEW_PRODUCTS",
        "VIEW_CUSTOMERS",
        "VIEW_RFM",
        "VIEW_COHORTS",
        "VIEW_RETURNS",
        "VIEW_INVENTORY",
        "VIEW_TARGETS",
        "VIEW_FORECAST",
        "EXPORT_DATA",
    },

    "Emirate Manager": {
        "VIEW_EXECUTIVE",
        "VIEW_SALES",
        "VIEW_STORES",
        "VIEW_PRODUCTS",
        "VIEW_CUSTOMERS",
        "VIEW_RETURNS",
        "VIEW_INVENTORY",
        "VIEW_TARGETS",
        "EXPORT_DATA",
    },

    "Store Manager": {
        "VIEW_SALES",
        "VIEW_STORES",
        "VIEW_PRODUCTS",
        "VIEW_CUSTOMERS",
        "VIEW_RETURNS",
        "VIEW_INVENTORY",
        "VIEW_TARGETS",
        "EXPORT_DATA",
    },

    "Sales Analyst": {
        "VIEW_SALES",
        "VIEW_STORES",
        "VIEW_PRODUCTS",
        "VIEW_CUSTOMERS",
        "VIEW_RFM",
        "VIEW_COHORTS",
        "VIEW_RETURNS",
        "VIEW_FORECAST",
        "EXPORT_DATA",
    },

    "Inventory Analyst": {
        "VIEW_PRODUCTS",
        "VIEW_RETURNS",
        "VIEW_INVENTORY",
        "EXPORT_DATA",
    },

    "Admin": {
        "MANAGE_USERS",
    },
}


DEMO_USERS = [
    {
        "username":
            "ceo",

        "email":
            "ceo@synthetic-retail.ae",

        "password_env":
            "DEMO_CEO_PASSWORD",

        "role":
            "CEO",

        "scope_type":
            "ALL",
    },

    {
        "username":
            "dubai.manager",

        "email":
            "dubai.manager@synthetic-retail.ae",

        "password_env":
            "DEMO_DUBAI_MANAGER_PASSWORD",

        "role":
            "Emirate Manager",

        "scope_type":
            "EMIRATE",

        "emirate_name":
            "Dubai",
    },

    {
        "username":
            "store.manager",

        "email":
            "store.manager@synthetic-retail.ae",

        "password_env":
            "DEMO_STORE_MANAGER_PASSWORD",

        "role":
            "Store Manager",

        "scope_type":
            "STORE",

        "store_code":
            "STR001",
    },

    {
        "username":
            "inventory.analyst",

        "email":
            "inventory.analyst@synthetic-retail.ae",

        "password_env":
            "DEMO_INVENTORY_PASSWORD",

        "role":
            "Inventory Analyst",

        "scope_type":
            "ALL",
    },
]


def required_password(
    environment_variable: str,
) -> str:
    password = os.getenv(
        environment_variable
    )

    if not password:
        raise RuntimeError(
            "Missing required environment "
            f"variable: {environment_variable}"
        )

    if password == "SET_LOCALLY":
        raise RuntimeError(
            f"{environment_variable} must "
            "be replaced with a local password."
        )

    return password


def main() -> None:
    print("=" * 78)
    print(
        "UAE Retail Intelligence Platform"
    )
    print(
        "STEP 23 - SECURITY SEED"
    )
    print("=" * 78)

    # Validate secrets before touching DB.
    user_passwords = {
        user[
            "username"
        ]:
            required_password(
                user[
                    "password_env"
                ]
            )
        for user in DEMO_USERS
    }

    engine = get_engine()

    with engine.begin() as connection:
        existing_counts = (
            connection.execute(
                text(
                    """
                    SELECT
                        (
                            SELECT COUNT(*)
                            FROM security.AppUser
                        ) AS Users,

                        (
                            SELECT COUNT(*)
                            FROM security.Role
                        ) AS Roles,

                        (
                            SELECT COUNT(*)
                            FROM security.Permission
                        ) AS Permissions
                    """
                )
            )
            .mappings()
            .one()
        )

        if (
            existing_counts[
                "Users"
            ]
            > 0
            or existing_counts[
                "Roles"
            ]
            > 0
            or existing_counts[
                "Permissions"
            ]
            > 0
        ):
            raise RuntimeError(
                "Security seed cancelled. "
                "Security tables already "
                "contain data."
            )

        # ----------------------------------------------------
        # Roles
        # ----------------------------------------------------

        for (
            role_name,
            description,
        ) in ROLES:
            connection.execute(
                text(
                    """
                    INSERT INTO security.Role
                    (
                        RoleName,
                        Description
                    )
                    VALUES
                    (
                        :role_name,
                        :description
                    )
                    """
                ),
                {
                    "role_name":
                        role_name,

                    "description":
                        description,
                },
            )

        # ----------------------------------------------------
        # Permissions
        # ----------------------------------------------------

        for (
            permission_code,
            permission_name,
        ) in PERMISSIONS:
            connection.execute(
                text(
                    """
                    INSERT INTO security.Permission
                    (
                        PermissionCode,
                        PermissionName,
                        Description
                    )
                    VALUES
                    (
                        :code,
                        :name,
                        :description
                    )
                    """
                ),
                {
                    "code":
                        permission_code,

                    "name":
                        permission_name,

                    "description":
                        permission_name,
                },
            )

        role_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        RoleId,
                        RoleName
                    FROM security.Role
                    """
                )
            )
            .mappings()
            .all()
        )

        role_lookup = {
            row[
                "RoleName"
            ]:
                row[
                    "RoleId"
                ]
            for row in role_rows
        }

        permission_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        PermissionId,
                        PermissionCode
                    FROM security.Permission
                    """
                )
            )
            .mappings()
            .all()
        )

        permission_lookup = {
            row[
                "PermissionCode"
            ]:
                row[
                    "PermissionId"
                ]
            for row in permission_rows
        }

        # ----------------------------------------------------
        # Role Permissions
        # ----------------------------------------------------

        for (
            role_name,
            permissions,
        ) in ROLE_PERMISSIONS.items():
            role_id = (
                role_lookup[
                    role_name
                ]
            )

            for code in sorted(
                permissions
            ):
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            security.RolePermission
                        (
                            RoleId,
                            PermissionId
                        )
                        VALUES
                        (
                            :role_id,
                            :permission_id
                        )
                        """
                    ),
                    {
                        "role_id":
                            role_id,

                        "permission_id":
                            permission_lookup[
                                code
                            ],
                    },
                )

        # ----------------------------------------------------
        # Demo Users
        # ----------------------------------------------------

        for user in DEMO_USERS:
            password_hash = (
                hash_password(
                    user_passwords[
                        user[
                            "username"
                        ]
                    ]
                )
            )

            result = (
                connection.execute(
                    text(
                        """
                        INSERT INTO security.AppUser
                        (
                            Username,
                            Email,
                            PasswordHash,
                            IsActive
                        )
                        OUTPUT INSERTED.UserId
                        VALUES
                        (
                            :username,
                            :email,
                            :password_hash,
                            1
                        )
                        """
                    ),
                    {
                        "username":
                            user[
                                "username"
                            ],

                        "email":
                            user[
                                "email"
                            ],

                        "password_hash":
                            password_hash,
                    },
                )
            )

            user_id = int(
                result.scalar_one()
            )

            role_id = int(
                role_lookup[
                    user[
                        "role"
                    ]
                ]
            )

            connection.execute(
                text(
                    """
                    INSERT INTO
                        security.UserRole
                    (
                        UserId,
                        RoleId
                    )
                    VALUES
                    (
                        :user_id,
                        :role_id
                    )
                    """
                ),
                {
                    "user_id":
                        user_id,

                    "role_id":
                        role_id,
                },
            )

            scope_type = (
                user[
                    "scope_type"
                ]
            )

            emirate_id = None
            store_id = None

            if (
                scope_type
                == "EMIRATE"
            ):
                emirate_id = int(
                    connection.execute(
                        text(
                            """
                            SELECT EmirateId
                            FROM core.Emirate
                            WHERE
                                EmirateName
                                = :name
                            """
                        ),
                        {
                            "name":
                                user[
                                    "emirate_name"
                                ]
                        },
                    ).scalar_one()
                )

            elif (
                scope_type
                == "STORE"
            ):
                store_id = int(
                    connection.execute(
                        text(
                            """
                            SELECT StoreId
                            FROM core.Store
                            WHERE
                                StoreCode
                                = :code
                            """
                        ),
                        {
                            "code":
                                user[
                                    "store_code"
                                ]
                        },
                    ).scalar_one()
                )

            connection.execute(
                text(
                    """
                    INSERT INTO
                        security.UserDataScope
                    (
                        UserId,
                        ScopeType,
                        EmirateId,
                        StoreId,
                        IsActive
                    )
                    VALUES
                    (
                        :user_id,
                        :scope_type,
                        :emirate_id,
                        :store_id,
                        1
                    )
                    """
                ),
                {
                    "user_id":
                        user_id,

                    "scope_type":
                        scope_type,

                    "emirate_id":
                        emirate_id,

                    "store_id":
                        store_id,
                },
            )

    print(
        "Roles       : "
        f"{len(ROLES)}"
    )

    print(
        "Permissions : "
        f"{len(PERMISSIONS)}"
    )

    print(
        "Demo Users  : "
        f"{len(DEMO_USERS)}"
    )

    print(
        "Passwords   : Argon2 hashes only"
    )

    print("-" * 78)

    print(
        "SECURITY SEED: SUCCESS"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()