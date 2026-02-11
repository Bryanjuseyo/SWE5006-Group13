from functools import wraps
from flask import request, jsonify, g
from jwt import ExpiredSignatureError, InvalidTokenError

from app.services.jwt_service import decode_token  # your decode helper


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "unauthorized", "message": "Missing Bearer token."}), 401

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except ExpiredSignatureError:
            return jsonify({"error": "unauthorized", "message": "Token has expired."}), 401
        except InvalidTokenError:
            return jsonify({"error": "unauthorized", "message": "Invalid token."}), 401

        g.user = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = (getattr(g, "user", {}) or {}).get("role")
            if role not in allowed_roles:
                return jsonify({"error": "forbidden", "message": "Access denied."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
