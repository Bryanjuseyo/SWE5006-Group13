import pytest
import jwt
from datetime import datetime, timedelta, timezone

from app.services.jwt_service import (
    generate_token,
    decode_token,
    generate_2fa_temp_token,
    decode_2fa_temp_token,
)


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


# ---------------------------------------------------------------------------
# generate_token
# ---------------------------------------------------------------------------

def test_generate_token_returns_string():
    token = generate_token(1, "user@test.com", "end_user")
    assert isinstance(token, str)
    assert len(token) > 20


def test_generate_token_payload_contains_fields(app):
    token = generate_token(7, "user@test.com", "cleaner")
    secret = app.config["JWT_SECRET"]
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    assert payload["user_id"] == 7
    assert payload["email"] == "user@test.com"
    assert payload["role"] == "cleaner"


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------

def test_decode_token_round_trip():
    token = generate_token(42, "decode@test.com", "end_user")
    payload = decode_token(token)
    assert payload["user_id"] == 42
    assert payload["email"] == "decode@test.com"
    assert payload["role"] == "end_user"


def test_decode_token_raises_on_expired(app):
    secret = app.config["JWT_SECRET"]
    now = datetime.now(timezone.utc)
    expired_payload = {
        "user_id": 1,
        "email": "x@test.com",
        "role": "end_user",
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "exp": int((now - timedelta(hours=1)).timestamp()),
    }
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_decode_token_raises_on_invalid_signature(app):
    token = generate_token(1, "user@test.com", "end_user")
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])


# ---------------------------------------------------------------------------
# generate_2fa_temp_token
# ---------------------------------------------------------------------------

def test_generate_2fa_temp_token_returns_string():
    token = generate_2fa_temp_token(5)
    assert isinstance(token, str)
    assert len(token) > 10


# ---------------------------------------------------------------------------
# decode_2fa_temp_token
# ---------------------------------------------------------------------------

def test_decode_2fa_temp_token_round_trip():
    token = generate_2fa_temp_token(99)
    payload = decode_2fa_temp_token(token)
    assert payload["user_id"] == 99
    assert payload["purpose"] == "2fa_verify"


def test_decode_2fa_temp_token_raises_on_wrong_purpose(app):
    secret = app.config["JWT_SECRET"]
    now = datetime.now(timezone.utc)
    bad_payload = {
        "user_id": 1,
        "purpose": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    token = jwt.encode(bad_payload, secret, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_2fa_temp_token(token)
