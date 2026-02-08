from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    try:
        result = AuthService.register_user(
            email=data.get("email"),
            password=data.get("password"),
            role_raw=data.get("role"),
        )
        return jsonify(result), 201

    except ValueError as e:
        # Format: "error_code|message"
        raw = str(e)
        if "|" in raw:
            error, message = raw.split("|", 1)
        else:
            error, message = "bad_request", raw

        status = 409 if error == "duplicate_email" else 400
        return jsonify({"error": error, "message": message}), status
