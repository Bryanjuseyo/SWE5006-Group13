import pytest
from jwt import ExpiredSignatureError, InvalidTokenError
from flask import Blueprint, jsonify, g
from app.api.auth.decorators import jwt_required


def test_jwt_required_missing_bearer_token_returns_401(app, client):
    bp = Blueprint("jwt_test_401", __name__)

    @bp.get("/api/_jwt_missing_bearer")
    @jwt_required
    def _jwt_missing_bearer():
        return jsonify(ok=True), 200

    app.register_blueprint(bp)

    res = client.get("/api/_jwt_missing_bearer")  # no header
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Missing Bearer token."


@pytest.mark.parametrize("auth_value", [
    "Token abc",
    "Bearer",       # missing token
    "bearer abc",   # wrong case
    "Bearerabc",    # missing space
    "",
])
def test_jwt_required_non_bearer_format_returns_401(app, client, auth_value):
    bp = Blueprint("jwt_test_non_bearer", __name__)

    @bp.get("/api/_jwt_non_bearer")
    @jwt_required
    def _jwt_non_bearer():
        return jsonify(ok=True), 200

    app.register_blueprint(bp)

    res = client.get("/api/_jwt_non_bearer", headers={"Authorization": auth_value})
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert "Missing Bearer token" in body["message"]


def test_jwt_required_expired_token_returns_401(app, client, patch_decode_token, bearer_header):
    bp = Blueprint("jwt_test_expired", __name__)

    @bp.get("/api/_jwt_expired")
    @jwt_required
    def _jwt_expired():
        return jsonify(ok=True), 200

    app.register_blueprint(bp)

    patch_decode_token(exc=ExpiredSignatureError())
    res = client.get("/api/_jwt_expired", headers=bearer_header("expired"))
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Token has expired."


def test_jwt_required_invalid_token_returns_401(app, client, patch_decode_token, bearer_header):
    bp = Blueprint("jwt_test_invalid", __name__)

    @bp.get("/api/_jwt_invalid")
    @jwt_required
    def _jwt_invalid():
        return jsonify(ok=True), 200

    app.register_blueprint(bp)

    patch_decode_token(exc=InvalidTokenError())
    res = client.get("/api/_jwt_invalid", headers=bearer_header("invalid"))
    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "unauthorized"
    assert body["message"] == "Invalid token."


def test_jwt_required_sets_g_user(app, client, patch_decode_token, bearer_header):
    bp = Blueprint("jwt_test_success", __name__)

    @bp.get("/api/_jwt_success")
    @jwt_required
    def _jwt_success():
        return jsonify(g_user=g.user), 200

    app.register_blueprint(bp)

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
