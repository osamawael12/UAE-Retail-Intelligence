"""
UAE Retail Intelligence Platform
Application Authentication Service

Responsibilities:
- Authenticate users
- Verify Argon2 password hashes
- Reject disabled users
- Track failed logins
- Reset failures on success
- Load roles
- Load permissions
- Load data scopes
- Write audit records
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text

from src.database.connection import (
    get_engine,
)
from src.security.passwords import (
    password_needs_rehash,
    verify_password,
)


@dataclass
class AuthenticatedUser:
    user_id: int
    username: str
    email: str
    roles: set[str]
    permissions: set[str]
    scopes: list[dict]

    def has_permission(
        self,
        permission_code: str,
    ) -> bool:
        return (
            permission_code
            in self.permissions
        )


def _audit(
    connection,
    user_id: int | None,
    event_type: str,
    success: bool,
    details: str | None = None,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO security.AuditLog
            (
                UserId,
                EventType,
                Success,
                Details
            )
            VALUES
            (
                :user_id,
                :event_type,
                :success,
                :details
            )
            """
        ),
        {
            "user_id":
                user_id,

            "event_type":
                event_type,

            "success":
                1 if success else 0,

            "details":
                details,
        },
    )


def authenticate(
    username: str,
    password: str,
) -> AuthenticatedUser | None:
    username = (
        username.strip()
    )

    if (
        not username
        or not password
    ):
        return None

    engine = get_engine()

    with engine.begin() as connection:
        user_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        UserId,
                        Username,
                        Email,
                        PasswordHash,
                        IsActive
                    FROM security.AppUser
                    WHERE
                        Username
                        = :username
                    """
                ),
                {
                    "username":
                        username
                },
            )
            .mappings()
            .first()
        )

        if user_row is None:
            _audit(
                connection=connection,
                user_id=None,
                event_type=(
                    "LOGIN_FAILED"
                ),
                success=False,
                details=(
                    "Unknown username"
                ),
            )

            return None

        user_id = int(
            user_row[
                "UserId"
            ]
        )

        if not bool(
            user_row[
                "IsActive"
            ]
        ):
            _audit(
                connection=connection,
                user_id=user_id,
                event_type=(
                    "LOGIN_FAILED"
                ),
                success=False,
                details=(
                    "Disabled user"
                ),
            )

            return None

        valid_password = (
            verify_password(
                password_hash=(
                    user_row[
                        "PasswordHash"
                    ]
                ),
                password=password,
            )
        )

        if not valid_password:
            connection.execute(
                text(
                    """
                    UPDATE security.AppUser

                    SET
                        FailedLoginCount
                            = FailedLoginCount
                              + 1,

                        UpdatedAt
                            = SYSUTCDATETIME()

                    WHERE
                        UserId
                        = :user_id
                    """
                ),
                {
                    "user_id":
                        user_id
                },
            )

            _audit(
                connection=connection,
                user_id=user_id,
                event_type=(
                    "LOGIN_FAILED"
                ),
                success=False,
                details=(
                    "Invalid password"
                ),
            )

            return None

        connection.execute(
            text(
                """
                UPDATE security.AppUser

                SET
                    FailedLoginCount = 0,

                    LastLoginAt
                        = SYSUTCDATETIME(),

                    UpdatedAt
                        = SYSUTCDATETIME()

                WHERE
                    UserId
                    = :user_id
                """
            ),
            {
                "user_id":
                    user_id
            },
        )

        role_rows = (
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
                        user_id
                },
            )
            .scalars()
            .all()
        )

        permission_rows = (
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

                    INNER JOIN
                        security.Permission p
                        ON rp.PermissionId
                           = p.PermissionId

                    WHERE
                        ur.UserId
                        = :user_id
                    """
                ),
                {
                    "user_id":
                        user_id
                },
            )
            .scalars()
            .all()
        )

        scope_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        ScopeType,
                        EmirateId,
                        StoreId

                    FROM security.UserDataScope

                    WHERE
                        UserId
                        = :user_id

                        AND IsActive = 1
                    """
                ),
                {
                    "user_id":
                        user_id
                },
            )
            .mappings()
            .all()
        )

        _audit(
            connection=connection,
            user_id=user_id,
            event_type=(
                "LOGIN_SUCCESS"
            ),
            success=True,
            details=None,
        )

        return AuthenticatedUser(
            user_id=user_id,

            username=str(
                user_row[
                    "Username"
                ]
            ),

            email=str(
                user_row[
                    "Email"
                ]
            ),

            roles=set(
                role_rows
            ),

            permissions=set(
                permission_rows
            ),

            scopes=[
                dict(row)
                for row
                in scope_rows
            ],
        )