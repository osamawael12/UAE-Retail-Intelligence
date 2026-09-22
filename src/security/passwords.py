"""
UAE Retail Intelligence Platform
Password Security

Uses Argon2id for application password hashing.

Plain-text passwords are never stored in SQL Server.
"""

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(
    password: str,
) -> str:
    if not isinstance(
        password,
        str,
    ):
        raise TypeError(
            "Password must be a string."
        )

    if len(password) < 10:
        raise ValueError(
            "Password must contain at "
            "least 10 characters."
        )

    return _password_hasher.hash(
        password
    )


def verify_password(
    password_hash: str,
    password: str,
) -> bool:
    try:
        return _password_hasher.verify(
            password_hash,
            password,
        )

    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):
        return False


def password_needs_rehash(
    password_hash: str,
) -> bool:
    try:
        return (
            _password_hasher
            .check_needs_rehash(
                password_hash
            )
        )

    except InvalidHashError:
        return True