from flask import Blueprint, request, jsonify, g
from app.api.auth.decorators import jwt_required
from app.services.profile_service import ProfileService

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/profile")
@jwt_required
def get_profile():
    user_id = g.user["user_id"]
    result = ProfileService.get_profile(user_id)
    return jsonify(result), 200


@profile_bp.put("/profile")
@jwt_required
def update_profile():
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}

    try:
        result = ProfileService.upsert_profile(user_id, data)
        return jsonify(result), 200
    except ValueError as e:
        raw = str(e)
        if "|" in raw:
            error, message = raw.split("|", 1)
        else:
            error, message = "bad_request", raw
        return jsonify({"error": error, "message": message}), 400
