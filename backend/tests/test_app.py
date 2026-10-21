from __future__ import annotations

from app.db import SessionLocal
from app.models.catalog import CatalogItem
from app.models.owned import OwnedItem


def test_app_imports():
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert {"/api/v1/ping", "/api/v1/queue", "/api/v1/history", "/api/v1/system/status"} <= paths


def test_ping(client):
    r = client.get("/api/v1/ping")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_api_requires_auth(client):
    assert client.get("/api/v1/queue").status_code == 401


def test_system_status_shows_version_and_sqlite(client, api_headers):
    r = client.get("/api/v1/system/status", headers=api_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.0.0-test"
    assert body["dbType"] == "sqlite"
    assert body["dbOk"] is True
    assert not any("budget" in k.lower() or "bricklink" in k.lower() for k in body)
    assert set(body["sources"]) == {"brickset"}


def test_health_has_no_bricklink_items(client, api_headers):
    r = client.get("/api/v1/health", headers=api_headers)
    assert r.status_code == 200
    assert all(item["source"] != "BrickLink" for item in r.json())


def test_add_set_refused_until_catalogue_source(client, api_headers):
    r = client.post("/api/v1/sets", json={"setNumber": "10281-1"}, headers=api_headers)
    assert r.status_code == 503
    assert r.json() == {"error": "ServiceUnavailable", "message": "Catalogue source arrives in BR.DK.09"}
    with SessionLocal() as db:
        assert db.query(OwnedItem).count() == 0
        assert db.query(CatalogItem).count() == 0


def test_fernet_round_trip():
    from app.crypto import decrypt_secret, encrypt_secret

    assert decrypt_secret(encrypt_secret("round trip")) == "round trip"
