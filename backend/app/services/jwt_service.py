from datetime import datetime, timedelta, timezone
import jwt
from flask import current_app

TWO_FA_TOKEN_EXPIRY_MINUTES = 5


def generate_token(user_id: int, email: str, role: str) -> str:
    hours = int(current_app.config.get("JWT_EXP_HOURS", 24))
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
    }
    secret = current_app.config["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    secret = current_app.config["JWT_SECRET"]
    return jwt.decode(token, secret, algorithms=["HS256"])


def generate_2fa_temp_token(user_id: int) -> str:
    """Short-lived token (5 min) used to complete the 2FA login step."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "purpose": "2fa_verify",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TWO_FA_TOKEN_EXPIRY_MINUTES)).timestamp()),
    }
    secret = current_app.config["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_2fa_temp_token(token: str) -> dict:
    """Decode a 2FA temp token and validate its purpose claim."""
    secret = current_app.config["JWT_SECRET"]
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    if payload.get("purpose") != "2fa_verify":
        raise jwt.InvalidTokenError("Invalid token purpose")
    return payload
