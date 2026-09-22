"""
UAE Retail Intelligence Platform
SQL Server SESSION_CONTEXT Management

Purpose:
- Bind an authenticated application UserId to a SQL connection.
- Allow SQL Server Row-Level Security to determine data scope.
- Clear SESSION_CONTEXT before returning pooled connections.

Important:
SESSION_CONTEXT is connection/session scoped.

Because SQLAlchemy uses connection pooling, the context MUST
be cleared before the connection is returned to the pool.
Otherwise one application user's identity could leak into
another user's database session.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text
from sqlalchemy.engine import (
    Connection,
    Engine,
)

from src.database.connection import (
    get_engine,
)


SESSION_USER_KEY = "UserId"


def set_user_context(
    connection: Connection,
    user_id: int,
) -> None:
    """
    Store authenticated application UserId in SQL Server
    SESSION_CONTEXT for the current SQL connection.
    """

    if not isinstance(
        user_id,
        int,
    ):
        raise TypeError(
            "user_id must be an integer."
        )

    if user_id <= 0:
        raise ValueError(
            "user_id must be positive."
        )

    connection.execute(
        text(
            """
            EXEC sys.sp_set_session_context
                @key = N'UserId',
                @value = :user_id;
            """
        ),
        {
            "user_id":
                user_id
        },
    )


def clear_user_context(
    connection: Connection,
) -> None:
    """
    Remove application UserId from the current SQL session.
    """

    connection.execute(
        text(
            """
            EXEC sys.sp_set_session_context
                @key = N'UserId',
                @value = NULL;
            """
        )
    )


def get_session_user_id(
    connection: Connection,
) -> int | None:
    """
    Read the UserId currently stored in SQL SESSION_CONTEXT.
    """

    value = connection.execute(
        text(
            """
            SELECT
                TRY_CONVERT(
                    INT,
                    SESSION_CONTEXT(
                        N'UserId'
                    )
                ) AS UserId;
            """
        )
    ).scalar_one()

    if value is None:
        return None

    return int(value)


@contextmanager
def user_database_connection(
    user_id: int,
    engine: Engine | None = None,
) -> Generator[
    Connection,
    None,
    None,
]:
    """
    Secure application database connection.

    Lifecycle:

    Checkout connection
        ↓
    Set SESSION_CONTEXT UserId
        ↓
    Execute application queries
        ↓
    Clear UserId
        ↓
    Return connection to pool

    Always use this context manager for RLS-aware application
    queries once RLS is enabled.
    """

    database_engine = (
        engine
        if engine is not None
        else get_engine()
    )

    connection = (
        database_engine.connect()
    )

    transaction = (
        connection.begin()
    )

    try:
        set_user_context(
            connection=connection,
            user_id=user_id,
        )

        context_user_id = (
            get_session_user_id(
                connection
            )
        )

        if (
            context_user_id
            != user_id
        ):
            raise RuntimeError(
                "Failed to establish "
                "SQL SESSION_CONTEXT."
            )

        yield connection

        transaction.commit()

    except Exception:
        transaction.rollback()
        raise

    finally:
        # Clear context in a fresh transaction because the
        # business transaction may already have been committed
        # or rolled back.
        try:
            if connection.in_transaction():
                connection.rollback()

            cleanup = (
                connection.begin()
            )

            try:
                clear_user_context(
                    connection
                )

                cleanup.commit()

            except Exception:
                cleanup.rollback()
                raise

        finally:
            connection.close()