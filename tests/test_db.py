import base64
import io
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from backend import db


def _encode_wallet(files: dict[str, bytes]) -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as wallet_zip:
        for filename, contents in files.items():
            wallet_zip.writestr(filename, contents)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_connection_config_maps_all_required_secrets(monkeypatch):
    secret_values = {
        "user": "test-user",
        "password": "test-password",
        "dsn": "test-dsn",
        "wallet_password": "test-wallet-password",
        "wallet_b64": "test-wallet",
    }
    monkeypatch.setattr(
        db,
        "_get_oracle_secret",
        lambda secret_name, _env_name: secret_values.get(secret_name),
    )

    config = db._get_connection_config()

    assert config == {
        "ORACLE_USER": "test-user",
        "ORACLE_PASSWORD": "test-password",
        "ORACLE_DSN": "test-dsn",
        "ORACLE_WALLET_PASSWORD": "test-wallet-password",
        "ORACLE_WALLET_B64": "test-wallet",
    }


def test_connection_config_reports_missing_values(monkeypatch):
    monkeypatch.setattr(
        db,
        "_get_oracle_secret",
        lambda secret_name, _env_name: None if secret_name == "password" else "value",
    )

    with pytest.raises(RuntimeError, match="ORACLE_PASSWORD"):
        db._get_connection_config()


def test_wallet_is_materialized_with_only_required_files(monkeypatch, tmp_path):
    wallet_secret = _encode_wallet(
        {
            "nested/tnsnames.ora": b"network aliases",
            "nested/ewallet.pem": b"encrypted wallet",
            "nested/ignored.txt": b"not required at runtime",
        }
    )
    wallet_directory = tmp_path / "wallet"

    def make_wallet_directory(prefix):
        assert prefix == "oracle_wallet_"
        wallet_directory.mkdir()
        return str(wallet_directory)

    monkeypatch.setattr(db.tempfile, "mkdtemp", make_wallet_directory)

    result = Path(db._materialize_base64_wallet(wallet_secret))

    assert result == wallet_directory
    assert (result / "tnsnames.ora").read_bytes() == b"network aliases"
    assert (result / "ewallet.pem").read_bytes() == b"encrypted wallet"
    assert not (result / "ignored.txt").exists()


@pytest.mark.parametrize(
    ("wallet_secret", "expected_message"),
    [
        ("not-valid-base64", "valid Base64"),
        (base64.b64encode(b"not a zip").decode("ascii"), "valid ZIP"),
        (_encode_wallet({"tnsnames.ora": b"aliases"}), "ewallet.pem"),
    ],
)
def test_invalid_wallet_is_rejected(wallet_secret, expected_message):
    with pytest.raises(RuntimeError, match=expected_message):
        db._materialize_base64_wallet(wallet_secret)


def test_run_query_sorts_parameters_for_stable_cache_keys(monkeypatch):
    captured = {}

    def fake_cached_query(sql, params_items):
        captured["sql"] = sql
        captured["params_items"] = params_items
        return pd.DataFrame({"ok": [1]})

    monkeypatch.setattr(db, "_run_query_cached", fake_cached_query)

    result = db.run_query("SELECT :a, :b FROM dual", {"b": 2, "a": 1})

    assert result.to_dict(orient="records") == [{"ok": 1}]
    assert captured == {
        "sql": "SELECT :a, :b FROM dual",
        "params_items": (("a", 1), ("b", 2)),
    }


@pytest.mark.parametrize(("query_result", "expected"), [([1], True), ([], False)])
def test_connection_check(monkeypatch, query_result, expected):
    monkeypatch.setattr(
        db,
        "run_query",
        lambda _sql: pd.DataFrame({"ok": query_result}),
    )

    assert db.test_connection() is expected
