import os
from pathlib import Path

import oracledb
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "3600"))
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "128"))
ORACLE_POOL_MAX = int(os.getenv("ORACLE_POOL_MAX", "4"))
CURSOR_ARRAY_SIZE = int(os.getenv("ORACLE_CURSOR_ARRAY_SIZE", "1000"))


def _get_connection_config():
    """Read and validate the Oracle Autonomous configuration."""

    config = {
        "ORACLE_USER": os.getenv("ORACLE_USER"),
        "ORACLE_PASSWORD": os.getenv("ORACLE_PASSWORD"),
        "ORACLE_DSN": os.getenv("ORACLE_DSN"),
        "ORACLE_WALLET_PATH": os.getenv("ORACLE_WALLET_PATH"),
        "ORACLE_WALLET_PASSWORD": os.getenv("ORACLE_WALLET_PASSWORD"),
    }

    required_vars = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
    missing = [name for name in required_vars if not config[name]]
    if missing:
        raise RuntimeError(
            f"Faltan variables en el archivo .env: {', '.join(missing)}"
        )

    wallet_path = config["ORACLE_WALLET_PATH"]
    wallet_password = config["ORACLE_WALLET_PASSWORD"]
    if bool(wallet_path) != bool(wallet_password):
        raise RuntimeError(
            "ORACLE_WALLET_PATH y ORACLE_WALLET_PASSWORD deben configurarse "
            "juntas para usar mTLS."
        )

    return config


@st.cache_resource(show_spinner=False)
def get_connection_pool():
    """Keep a shared connection pool across Streamlit reruns and sessions."""

    config = _get_connection_config()
    pool_options = {
        "user": config["ORACLE_USER"],
        "password": config["ORACLE_PASSWORD"],
        "dsn": config["ORACLE_DSN"],
        "min": 1,
        "max": max(1, ORACLE_POOL_MAX),
        "increment": 1,
        "getmode": oracledb.POOL_GETMODE_WAIT,
        "wait_timeout": 10_000,
        "ping_interval": 60,
        "stmtcachesize": 50,
    }

    if config["ORACLE_WALLET_PATH"]:
        pool_options.update(
            {
                "config_dir": config["ORACLE_WALLET_PATH"],
                "wallet_location": config["ORACLE_WALLET_PATH"],
                "wallet_password": config["ORACLE_WALLET_PASSWORD"],
            }
        )

    return oracledb.create_pool(
        **pool_options,
    )


def get_connection():
    """Acquire a reusable connection from the pool."""

    return get_connection_pool().acquire()


@st.cache_data(
    ttl=QUERY_CACHE_TTL_SECONDS,
    max_entries=QUERY_CACHE_MAX_ENTRIES,
    show_spinner=False,
)
def _run_query_cached(sql: str, params_items: tuple) -> pd.DataFrame:
    params = dict(params_items)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.arraysize = CURSOR_ARRAY_SIZE
            cursor.prefetchrows = CURSOR_ARRAY_SIZE
            cursor.execute(sql, params)

            columns = [column[0].lower() for column in cursor.description]
            rows = cursor.fetchall()

    return pd.DataFrame.from_records(
        rows,
        columns=columns,
        coerce_float=True,
    )


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a cached SQL query and return a pandas DataFrame."""

    params_items = tuple(sorted((params or {}).items()))
    return _run_query_cached(sql, params_items)


def test_connection() -> bool:
    """Run a lightweight connectivity check."""

    df = run_query("SELECT 1 AS ok FROM dual")
    return not df.empty and int(df.loc[0, "ok"]) == 1
