from datetime import datetime, timedelta, timezone
import jwt
from flask import current_app

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
