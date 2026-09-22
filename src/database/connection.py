import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def get_connection_string() -> str:
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    driver = os.getenv("DB_DRIVER")

    trusted_connection = os.getenv(
        "DB_TRUSTED_CONNECTION",
        "yes"
    )

    trust_server_certificate = os.getenv(
        "DB_TRUST_SERVER_CERTIFICATE",
        "yes"
    )

    required_variables = {
        "DB_SERVER": server,
        "DB_NAME": database,
        "DB_DRIVER": driver,
    }

    missing_variables = [
        name
        for name, value in required_variables.items()
        if not value
    ]

    if missing_variables:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing_variables)
        )

    odbc_connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection={trusted_connection};"
        f"TrustServerCertificate={trust_server_certificate};"
    )

    return (
        "mssql+pyodbc:///?odbc_connect="
        + quote_plus(odbc_connection_string)
    )


def get_engine():
    return create_engine(
        get_connection_string(),
        pool_pre_ping=True,
        future=True,
    )