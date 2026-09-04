import base64
import binascii
import io
import os
import tempfile
import zipfile
from pathlib import Path

import oracledb
import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "3600"))
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "128"))
ORACLE_POOL_MAX = int(os.getenv("ORACLE_POOL_MAX", "4"))
CURSOR_ARRAY_SIZE = int(os.getenv("ORACLE_CURSOR_ARRAY_SIZE", "1000"))
WALLET_REQUIRED_FILES = ("tnsnames.ora", "ewallet.pem")
MAX_WALLET_FILE_SIZE = 5 * 1024 * 1024


def _get_oracle_secret(secret_name: str, env_name: str):
    try:
        return st.secrets["oracle"].get(secret_name)
    except (KeyError, StreamlitSecretNotFoundError):
        return os.getenv(env_name)


def _get_connection_config():
    """Read and validate the Oracle Autonomous configuration."""

    config = {
        "ORACLE_USER": _get_oracle_secret("user", "ORACLE_USER"),
        "ORACLE_PASSWORD": _get_oracle_secret("password", "ORACLE_PASSWORD"),
        "ORACLE_DSN": _get_oracle_secret("dsn", "ORACLE_DSN"),
        "ORACLE_WALLET_PASSWORD": _get_oracle_secret(
            "wallet_password",
            "ORACLE_WALLET_PASSWORD",
        ),
        "ORACLE_WALLET_B64": _get_oracle_secret(
            "wallet_b64",
            "ORACLE_WALLET_B64",
        ),
    }

    required_vars = (
        "ORACLE_USER",
        "ORACLE_PASSWORD",
        "ORACLE_DSN",
        "ORACLE_WALLET_PASSWORD",
        "ORACLE_WALLET_B64",
    )
    missing = [name for name in required_vars if not config[name]]
    if missing:
        raise RuntimeError(f"Missing configuration variables: {', '.join(missing)}")

    return config


def _materialize_base64_wallet(wallet_b64: str) -> str:
    """Decode the wallet secret into a private temporary directory."""

    try:
        wallet_bytes = base64.b64decode(
            "".join(wallet_b64.split()),
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(
            "ORACLE_WALLET_B64 does not contain valid Base64 data."
        ) from exc

    try:
        with zipfile.ZipFile(io.BytesIO(wallet_bytes)) as wallet_zip:
            members = {
                Path(info.filename).name: info
                for info in wallet_zip.infolist()
                if not info.is_dir()
            }

            missing = [
                filename
                for filename in WALLET_REQUIRED_FILES
                if filename not in members
            ]
            if missing:
                raise RuntimeError(
                    "The wallet does not contain the required files: "
                    + ", ".join(missing)
                )

            wallet_dir = Path(tempfile.mkdtemp(prefix="oracle_wallet_"))
            for filename in WALLET_REQUIRED_FILES:
                member = members[filename]
                if member.file_size > MAX_WALLET_FILE_SIZE:
                    raise RuntimeError(
                        f"The file {filename} exceeds the permitted size."
                    )

                target = wallet_dir / filename
                target.write_bytes(wallet_zip.read(member))
                try:
                    target.chmod(0o600)
                except OSError:
                    pass
    except zipfile.BadZipFile as exc:
        raise RuntimeError(
            "ORACLE_WALLET_B64 does not contain a valid ZIP file."
        ) from exc

    try:
        wallet_dir.chmod(0o700)
    except OSError:
        pass

    return str(wallet_dir)


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

    wallet_path = _materialize_base64_wallet(config["ORACLE_WALLET_B64"])
    pool_options.update(
        {
            "config_dir": wallet_path,
            "wallet_location": wallet_path,
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
