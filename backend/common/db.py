"""
Database helper functions for Homework 4 services.

All microservices use this module to obtain a SQLite connection to the
historical OHLCV data generated in Homework 3.

By default it points to the same `crypto_data.db` file that Homework 3 uses,
but the path can be overridden via the `CRYPTO_DB_PATH` environment variable.
"""

import os
import sqlite3
from typing import Generator

from .. import config


def get_db_path() -> str:
    """
    Returns the path to the SQLite database file.

    Priority:
    1. CRYPTO_DB_PATH environment variable
    2. config.DB_NAME (same as Homework 3)
    """
    return os.getenv("CRYPTO_DB_PATH", config.DB_NAME)


def get_connection() -> sqlite3.Connection:
    """
    Create a new SQLite connection using the configured database path.

    The connection uses `sqlite3.Row` as row_factory for convenient dict-like access.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def connection_scope() -> Generator[sqlite3.Connection, None, None]:
    """
    Context-style generator that yields a database connection and
    ensures it is closed afterwards.

    Example usage:
        with contextlib.closing(get_connection()) as conn:
            ...
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


