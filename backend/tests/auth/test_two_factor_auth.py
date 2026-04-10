"""
Unit tests for:
  US-33: End-User Two Factor Authentication
  US-34: Cleaner Two Factor Authentication
  US-35: Administrator Two Factor Authentication

All three user stories exercise the same 2FA routes — the platform does not
differentiate by role.  Parametrizing across roles covers all three stories.

Routes under test:
  GET  /api/auth/2fa/status   — check if 2FA is enabled
  POST /api/auth/2fa/setup    — generate and email an OTP
  POST /api/auth/2fa/enable   — verify OTP and enable 2FA
  POST /api/auth/2fa/disable  — verify password and disable 2FA
  POST /api/auth/2fa/verify   — verify login OTP (completes 2FA login flow)
"""
import pytest
from datetime import datetime, timezone, timedelta
from jwt import ExpiredSignatureError, InvalidTokenError


ALL_ROLES = ["end_user", "cleaner", "administrator"]

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _auth_headers(patch_decode_token, bearer_header, user_id=1, role="end_user"):
    patch_decode_token(payload={"user_id": user_id, "email": "u@test.com", "role": role})
    return bearer_header("ok")


def _patch_user_query(mocker, mock_user):
    """
    Patch User.query in the auth routes module.

    User.query is a SQLAlchemy descriptor — each access creates a new Query
    object, so patching User.query.get directly has no effect (the patched
    object is discarded on the next access).  We must replace User.query
    itself with a plain Mock so that .get() is reliably intercepted.
    """
    mock_q = mocker.Mock()
    mock_q.get.return_value = mock_user
    mocker.patch("app.api.auth.routes.User.query", mock_q)
    return mock_q


# ===========================================================================
# GET /api/auth/2fa/status
# US-33 / US-34 / US-35
# ===========================================================================

@pytest.mark.parametrize("role", ALL_ROLES)
def test_2fa_status_returns_current_state_for_any_role(
    client, patch_decode_token, bearer_header, mocker, role
):
    """US-33/34/35: any authenticated role can query their 2FA status."""
    headers = _auth_headers(patch_decode_token, bearer_header, user_id=1, role=role)

    mock_user = mocker.Mock()
    mock_user.two_factor_enabled = True
    _patch_user_query(mocker, mock_user)

    resp = client.get("/api/auth/2fa/status", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["two_factor_enabled"] is True


def test_2fa_status_returns_401_without_token(client):
    """US-33/34/35: unauthenticated request to status endpoint is rejected."""
    resp = client.get("/api/auth/2fa/status")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "unauthorized"


def test_2fa_status_returns_404_when_user_not_found(
    client, patch_decode_token, bearer_header, mocker
):
    """US-33/34/35: 404 returned if the user_id in the token no longer exists."""
    headers = _auth_headers(patch_decode_token, bearer_header)
    _patch_user_query(mocker, None)

    resp = client.get("/api/auth/2fa/status", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


# ===========================================================================
# POST /api/auth/2fa/setup
# US-33 / US-34 / US-35
# ===========================================================================

@pytest.mark.parametrize("role", ALL_ROLES)
def test_2fa_setup_sends_otp_email_for_any_role(
    client, patch_decode_token, bearer_header, mocker, role
):
    """US-33/34/35: OTP email is dispatched for every role during 2FA setup."""
    headers = _auth_headers(patch_decode_token, bearer_header, role=role)

    mock_user = mocker.Mock()
    mock_user.email = "u@test.com"
    _patch_user_query(mocker, mock_user)
    mocker.patch("app.api.auth.routes.TwoFactorService.generate_and_store_otp", return_value="123456")
    mock_send = mocker.patch("app.api.auth.routes.EmailService.send_otp_email")

    resp = client.post("/api/auth/2fa/setup", headers=headers)

    assert resp.status_code == 200
    assert "OTP" in resp.get_json()["message"]
    mock_send.assert_called_once_with("u@test.com", "123456", "2FA setup")


def test_2fa_setup_returns_401_without_token(client):
    """US-33/34/35: setup endpoint requires authentication."""
    resp = client.post("/api/auth/2fa/setup")
    assert resp.status_code == 401


# ===========================================================================
# POST /api/auth/2fa/enable
# US-33 / US-34 / US-35
# ===========================================================================

@pytest.mark.parametrize("role", ALL_ROLES)
def test_2fa_enable_succeeds_with_correct_otp_for_any_role(
    client, patch_decode_token, bearer_header, mocker, role
):
    """US-33/34/35: 2FA is enabled after the user submits the correct OTP."""
    headers = _auth_headers(patch_decode_token, bearer_header, role=role)

    mock_user = mocker.Mock()
    _patch_user_query(mocker, mock_user)
    mocker.patch("app.api.auth.routes.TwoFactorService.verify_otp")
    mocker.patch("app.api.auth.routes.db.session")

    resp = client.post("/api/auth/2fa/enable", headers=headers, json={"otp": "123456"})

    assert resp.status_code == 200
    assert mock_user.two_factor_enabled is True
    assert "enabled" in resp.get_json()["message"]


def test_2fa_enable_returns_400_with_incorrect_otp(
    client, patch_decode_token, bearer_header, mocker
):
    """US-33/34/35: incorrect OTP during enable returns 400."""
    headers = _auth_headers(patch_decode_token, bearer_header)

    mock_user = mocker.Mock()
    _patch_user_query(mocker, mock_user)
    mocker.patch(
        "app.api.auth.routes.TwoFactorService.verify_otp",
        side_effect=ValueError("invalid_otp|Incorrect OTP. Please try again.")
    )

    resp = client.post("/api/auth/2fa/enable", headers=headers, json={"otp": "000000"})

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_otp"


def test_2fa_enable_returns_400_with_expired_otp(
    client, patch_decode_token, bearer_header, mocker
):
    """US-33/34/35: expired OTP returns 400."""
    headers = _auth_headers(patch_decode_token, bearer_header)

    mock_user = mocker.Mock()
    _patch_user_query(mocker, mock_user)
    mocker.patch(
        "app.api.auth.routes.TwoFactorService.verify_otp",
        side_effect=ValueError("expired_otp|OTP has expired. Please request a new one.")
    )

    resp = client.post("/api/auth/2fa/enable", headers=headers, json={"otp": "123456"})

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "expired_otp"


# ===========================================================================
# POST /api/auth/2fa/disable
# US-33 / US-34 / US-35
# ===========================================================================

@pytest.mark.parametrize("role", ALL_ROLES)
def test_2fa_disable_succeeds_with_correct_password_for_any_role(
    client, patch_decode_token, bearer_header, mocker, role
):
    """US-33/34/35: 2FA is disabled after password is verified."""
    headers = _auth_headers(patch_decode_token, bearer_header, role=role)

    mock_user = mocker.Mock()
    mock_user.two_factor_enabled = True
    mock_user.check_password.return_value = True
    _patch_user_query(mocker, mock_user)
    mocker.patch("app.api.auth.routes.db.session")

    resp = client.post(
        "/api/auth/2fa/disable", headers=headers, json={"password": "Passw0rd!"}
    )

    assert resp.status_code == 200
    assert mock_user.two_factor_enabled is False
    assert "disabled" in resp.get_json()["message"]


def test_2fa_disable_returns_401_with_wrong_password(
    client, patch_decode_token, bearer_header, mocker
):
    """US-33/34/35: wrong password during disable returns 401."""
    headers = _auth_headers(patch_decode_token, bearer_header)

    mock_user = mocker.Mock()
    mock_user.two_factor_enabled = True
    mock_user.check_password.return_value = False
    _patch_user_query(mocker, mock_user)

    resp = client.post(
        "/api/auth/2fa/disable", headers=headers, json={"password": "WrongPass1"}
    )

    assert resp.status_code == 401
    assert resp.get_json()["error"] == "invalid_password"


def test_2fa_disable_returns_400_when_not_enabled(
    client, patch_decode_token, bearer_header, mocker
):
    """US-33/34/35: cannot disable 2FA that is not currently enabled."""
    headers = _auth_headers(patch_decode_token, bearer_header)

    mock_user = mocker.Mock()
    mock_user.two_factor_enabled = False
    _patch_user_query(mocker, mock_user)

    resp = client.post(
        "/api/auth/2fa/disable", headers=headers, json={"password": "Passw0rd!"}
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "not_enabled"


# ===========================================================================
# POST /api/auth/2fa/verify  (login OTP verification)
# US-33 / US-34 / US-35
# ===========================================================================

def test_2fa_verify_returns_jwt_on_correct_otp(client, mocker):
    """US-33/34/35: valid OTP during login returns a JWT token."""
    mock_payload = {"user_id": 1}
    mocker.patch("app.api.auth.routes.decode_2fa_temp_token", return_value=mock_payload)

    mock_user = mocker.Mock()
    mock_user.id = 1
    mock_user.email = "u@test.com"
    mock_user.role.value = "end_user"
    mock_user.to_dict.return_value = {"id": 1, "email": "u@test.com"}
    _patch_user_query(mocker, mock_user)
    mocker.patch("app.api.auth.routes.TwoFactorService.verify_otp")
    mocker.patch("app.api.auth.routes.db.session")
    mocker.patch("app.api.auth.routes.generate_token", return_value="jwt.token.here")

    resp = client.post(
        "/api/auth/2fa/verify",
        json={"otp": "123456", "temp_token": "valid.temp.token"}
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert "token" in body
    assert body["token"] == "jwt.token.here"
    assert "Login successful" in body["message"]


def test_2fa_verify_returns_401_on_incorrect_otp(client, mocker):
    """US-33/34/35: incorrect OTP during login verification returns 401."""
    mocker.patch("app.api.auth.routes.decode_2fa_temp_token", return_value={"user_id": 1})
    mock_user = mocker.Mock()
    _patch_user_query(mocker, mock_user)
    mocker.patch(
        "app.api.auth.routes.TwoFactorService.verify_otp",
        side_effect=ValueError("invalid_otp|Incorrect OTP. Please try again.")
    )

    resp = client.post(
        "/api/auth/2fa/verify",
        json={"otp": "000000", "temp_token": "valid.temp.token"}
    )

    assert resp.status_code == 401
    assert resp.get_json()["error"] == "invalid_otp"


def test_2fa_verify_returns_401_on_invalid_temp_token(client, mocker):
    """US-33/34/35: expired or tampered temp_token during login verification returns 401."""
    mocker.patch(
        "app.api.auth.routes.decode_2fa_temp_token",
        side_effect=ExpiredSignatureError()
    )

    resp = client.post(
        "/api/auth/2fa/verify",
        json={"otp": "123456", "temp_token": "expired.or.invalid"}
    )

    assert resp.status_code == 401
    assert resp.get_json()["error"] == "invalid_token"
