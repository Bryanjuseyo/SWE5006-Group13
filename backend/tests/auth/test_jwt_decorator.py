import pytest
from jwt import ExpiredSignatureError, InvalidTokenError


def test_jwt_required_missing_bearer_token_returns_401(client):
    res = client.get("/api/_jwt_missing_bearer")
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Missing Bearer token."


@pytest.mark.parametrize("auth_value", [
    "Token abc",
    "Bearer",
    "bearer abc",
    "Bearerabc",
    "",
])
def test_jwt_required_non_bearer_format_returns_401(client, auth_value):
    res = client.get("/api/_jwt_non_bearer", headers={"Authorization": auth_value})
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert "Missing Bearer token" in body["message"]


def test_jwt_required_expired_token_returns_401(client, patch_decode_token, bearer_header):
    patch_decode_token(exc=ExpiredSignatureError())
    res = client.get("/api/_jwt_expired", headers=bearer_header("expired"))
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Token has expired."


def test_jwt_required_invalid_token_returns_401(client, patch_decode_token, bearer_header):
    patch_decode_token(exc=InvalidTokenError())
    res = client.get("/api/_jwt_invalid", headers=bearer_header("invalid"))
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Invalid token."


def test_jwt_required_sets_g_user(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 123,
        "email": "x@test.com",
        "role": "administrator",
    })
    res = client.get("/api/_jwt_success", headers=bearer_header("ok"))
    assert res.status_code == 200
    body = res.get_json()
    assert body["g_user"]["user_id"] == 123
    assert body["g_user"]["email"] == "x@test.com"
    assert body["g_user"]["role"] == "administrator"
