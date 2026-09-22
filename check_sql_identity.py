from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

with engine.connect() as connection:
    row = connection.execute(
        text("""
            SELECT
                ORIGINAL_LOGIN() AS OriginalLogin,
                SUSER_SNAME() AS LoginName,
                USER_NAME() AS DatabaseUser,
                IS_ROLEMEMBER('db_owner') AS IsDbOwner
        """)
    ).mappings().one()

    print(dict(row))
