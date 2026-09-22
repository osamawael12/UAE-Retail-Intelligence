from sqlalchemy import text

from src.database.connection import get_engine


def main():
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    @@SERVERNAME AS ServerName,
                    DB_NAME() AS DatabaseName,
                    SUSER_SNAME() AS LoginName
                """
            )
        ).mappings().one()

    print("=" * 50)
    print("SQL Server connection successful.")
    print("=" * 50)

    print(f"Server   : {result['ServerName']}")
    print(f"Database : {result['DatabaseName']}")
    print(f"Login    : {result['LoginName']}")

    print("=" * 50)


if __name__ == "__main__":
    main()