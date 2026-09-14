import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / "emergency_simulation" / ".env.test")


@pytest.fixture
def database_connection():
    connection = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        dbname=os.getenv(
            "POSTGRES_DB",
            "emergency_simulation_test",
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "emergency_simulation_test",
        ),
        password=os.environ["POSTGRES_PASSWORD"],
    )
    # ************************
    # Now, each test gets an independent connection/transaction.
    # ************************
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()
