from flask import Blueprint, request, jsonify, g
from app.services.cleaner_profile_service import CleanerProfileService
from app.api.auth.decorators import jwt_required, roles_required

cleaner_bp = Blueprint("cleaner", __name__)


@cleaner_bp.before_request
@jwt_required
@roles_required("cleaner")
def _guard():
    pass


@cleaner_bp.get("/dashboard")
def dashboard():
    return jsonify(message="Cleaner dashboard")


@cleaner_bp.get("/profile")
def get_profile():
    user_id = g.user["user_id"]
    return jsonify(CleanerProfileService.get_cleaner_profile(user_id)), 200


@cleaner_bp.put("/profile")
def update_profile():
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(
            CleanerProfileService.upsert_cleaner_profile(user_id, data)
        ), 200
    except ValueError as e:
        error, message = str(e).split("|", 1)
        return jsonify({"error": error, "message": message}), 400
