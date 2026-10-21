from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings, secrets_from_files


def test_file_value_trims_exactly_one_newline(tmp_path):
    f = tmp_path / "value"
    f.write_text("value-from-file\n\n")
    assert secrets_from_files({"BRICKARR_DB_PASSWORD_FILE": str(f)}) == {"db_password": "value-from-file\n"}


def test_file_value_without_newline_or_with_crlf(tmp_path):
    plain = tmp_path / "plain"
    plain.write_text("abc")
    crlf = tmp_path / "crlf"
    crlf.write_bytes(b"abc\r\n")
    assert secrets_from_files({"BRICKARR_A_FILE": str(plain), "BRICKARR_B_FILE": str(crlf)}) == {"a": "abc", "b": "abc"}


def test_file_and_plain_value_together_are_refused(tmp_path):
    f = tmp_path / "value"
    f.write_text("x\n")
    with pytest.raises(RuntimeError, match="BRICKARR_DB_PASSWORD"):
        secrets_from_files({"BRICKARR_DB_PASSWORD_FILE": str(f), "BRICKARR_DB_PASSWORD": "y"})


def test_unrelated_variables_are_ignored():
    assert secrets_from_files({"PATH": "/bin", "BRICKARR_FILE": "/nope", "OTHER_X_FILE": "/nope"}) == {}


def test_file_value_reaches_settings(tmp_path):
    f = tmp_path / "value"
    f.write_text("value-from-file\n")
    s = Settings(**secrets_from_files({"BRICKARR_DB_PASSWORD_FILE": str(f)}))
    assert s.db_password == "value-from-file"


def test_cache_dir_defaults_to_library():
    assert Settings(library_dir="/srv/lego").cache_dir == Path("/srv/lego")
    assert Settings(library_dir="/srv/lego", cache_dir="").cache_dir == Path("/srv/lego")
    assert Settings(library_dir="/srv/lego", cache_dir="/cache").cache_dir == Path("/cache")


def test_sqlite_file_lives_in_config_dir():
    s = Settings(db_type="sqlite", config_dir="/config")
    assert s.db_url.drivername == "sqlite+pysqlite"
    assert s.db_url.database == "/config/brickarr.db"


def test_mariadb_url_keeps_awkward_password_intact():
    s = Settings(db_type="MariaDB", db_host="db", db_password="p@ss:w/rd%")
    assert s.db_type == "mariadb"
    url = s.db_url
    assert url.drivername == "mysql+pymysql"
    assert (url.host, url.port, url.database) == ("db", 3306, "brickarr")
    assert url.password == "p@ss:w/rd%"
    assert url.query["charset"] == "utf8mb4"
