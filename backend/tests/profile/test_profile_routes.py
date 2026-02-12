import pytest
from jwt import ExpiredSignatureError, InvalidTokenError


# ---------- AUTHN: 401 tests (profile only) ----------

@pytest.mark.parametrize("method", ["get", "put"])
def test_profile_missing_bearer_token_returns_401(client, method):
    if method == "get":
        resp = client.get("/api/profile")
    else:
        resp = client.put("/api/profile", json={"name": "abc"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"


@pytest.mark.parametrize("method", ["get", "put"])
def test_profile_non_bearer_authorization_returns_401(client, method):
    headers = {"Authorization": "Token abc"}
    if method == "get":
        resp = client.get("/api/profile", headers=headers)
    else:
        resp = client.put("/api/profile", headers=headers, json={"name": "abc"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"


@pytest.mark.parametrize("method", ["get", "put"])
def test_profile_expired_token_returns_401(client, patch_decode_token, bearer_header, method):
    patch_decode_token(exc=ExpiredSignatureError())
    if method == "get":
        resp = client.get("/api/profile", headers=bearer_header("expired"))
    else:
        resp = client.put("/api/profile", headers=bearer_header("expired"), json={"name": "abc"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"


@pytest.mark.parametrize("method", ["get", "put"])
def test_profile_invalid_token_returns_401(client, patch_decode_token, bearer_header, method):
    patch_decode_token(exc=InvalidTokenError())
    if method == "get":
        resp = client.get("/api/profile", headers=bearer_header("invalid"))
    else:
        resp = client.put("/api/profile", headers=bearer_header("invalid"), json={"name": "abc"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"


# ---------- HAPPY PATH: 200 tests (profile only) ----------

@pytest.mark.parametrize("role", ["cleaner", "end_user", "administrator"])
def test_any_logged_in_role_can_get_profile(client, patch_decode_token, bearer_header, mocker, role):
    patch_decode_token(payload={"user_id": 99, "email": "p@p.com", "role": role})
    mocker.patch("app.services.profile_service.ProfileService.get_profile", return_value={"user_id": 99})

    resp = client.get("/api/profile", headers=bearer_header("ok"))
    assert resp.status_code == 200
    assert resp.get_json()["user_id"] == 99


@pytest.mark.parametrize("role", ["cleaner", "end_user", "administrator"])
def test_any_logged_in_role_can_update_profile(client, patch_decode_token, bearer_header, mocker, role):
    patch_decode_token(payload={"user_id": 88, "email": "p@p.com", "role": role})
    mocker.patch("app.services.profile_service.ProfileService.upsert_profile", return_value={"ok": True})

    resp = client.put("/api/profile", headers=bearer_header("ok"), json={"name": "abc"})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
