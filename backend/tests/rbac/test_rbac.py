import pytest
from jwt import ExpiredSignatureError, InvalidTokenError


# ---------- AUTHN: 401 tests (dashboards only) ----------

@pytest.mark.parametrize("url", [
    "/api/cleaner/dashboard",
    "/api/end-user/dashboard",
    "/api/admin/dashboard",
])
def test_missing_bearer_token_returns_401(client, url):
    resp = client.get(url)
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"
    assert "Missing Bearer token" in data["message"]


@pytest.mark.parametrize("url", [
    "/api/cleaner/dashboard",
    "/api/end-user/dashboard",
    "/api/admin/dashboard",
])
def test_non_bearer_authorization_returns_401(client, url):
    resp = client.get(url, headers={"Authorization": "Token abc"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"


@pytest.mark.parametrize("url", [
    "/api/cleaner/dashboard",
    "/api/end-user/dashboard",
    "/api/admin/dashboard",
])
def test_expired_token_returns_401(client, patch_decode_token, bearer_header, url):
    patch_decode_token(exc=ExpiredSignatureError())
    resp = client.get(url, headers=bearer_header("expired"))
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"
    assert "expired" in data["message"].lower()


@pytest.mark.parametrize("url", [
    "/api/cleaner/dashboard",
    "/api/end-user/dashboard",
    "/api/admin/dashboard",
])
def test_invalid_token_returns_401(client, patch_decode_token, bearer_header, url):
    patch_decode_token(exc=InvalidTokenError())
    resp = client.get(url, headers=bearer_header("invalid"))
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "unauthorized"
    assert "invalid" in data["message"].lower()


# ---------- AUTHZ: 403 role tests ----------

@pytest.mark.parametrize("url, role", [
    ("/api/admin/dashboard", "cleaner"),
    ("/api/admin/dashboard", "end_user"),
    ("/api/cleaner/dashboard", "administrator"),
    ("/api/cleaner/dashboard", "end_user"),
    ("/api/end-user/dashboard", "administrator"),
    ("/api/end-user/dashboard", "cleaner"),
])
def test_wrong_role_cannot_access_dashboards_returns_403(client, patch_decode_token, bearer_header, url, role):
    patch_decode_token(payload={"user_id": 1, "email": "a@b.com", "role": role})
    resp = client.get(url, headers=bearer_header("ok"))
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "forbidden"
    assert "Access denied" in data["message"]


def test_missing_role_in_token_returns_403(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 1, "email": "a@b.com"})  # no role
    resp = client.get("/api/admin/dashboard", headers=bearer_header("ok"))
    assert resp.status_code == 403


# ---------- HAPPY PATH: 200 tests ----------

def test_cleaner_can_access_cleaner_dashboard(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 11, "email": "c@c.com", "role": "cleaner"})
    resp = client.get("/api/cleaner/dashboard", headers=bearer_header("ok"))
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Cleaner dashboard"


def test_end_user_can_access_end_user_dashboard(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 22, "email": "u@u.com", "role": "end_user"})
    resp = client.get("/api/end-user/dashboard", headers=bearer_header("ok"))
    assert resp.status_code == 200
    assert "Welcome end-user" in resp.get_json()["message"]


def test_admin_can_access_admin_dashboard(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 33, "email": "a@a.com", "role": "administrator"})
    resp = client.get("/api/admin/dashboard", headers=bearer_header("ok"))
    assert resp.status_code == 200
    assert "Welcome admin" in resp.get_json()["message"]
