from flask import Blueprint, request, jsonify, g
from app.services.cleaner_profile_service import CleanerProfileService
from app.api.auth.decorators import jwt_required, roles_required

cleaner_bp = Blueprint("cleaner", __name__)


@cleaner_bp.before_request
@jwt_required
def _guard():
    if request.method == "OPTIONS":
        return "", 204
    return None


@cleaner_bp.get("/dashboard")
@roles_required("cleaner")
def dashboard():
    return jsonify(message="Cleaner dashboard")


@cleaner_bp.get("/profile")
@jwt_required
@roles_required("cleaner")
def get_profile():
    user_id = g.user["user_id"]
    return jsonify(CleanerProfileService.get_cleaner_profile(user_id)), 200


@cleaner_bp.put("/profile")
@jwt_required
@roles_required("cleaner")
def update_profile():
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(CleanerProfileService.upsert_cleaner_profile(user_id, data)), 200
    except ValueError as e:
        raw = str(e)
        error, message = raw.split("|", 1) if "|" in raw else ("bad_request", raw)
        return jsonify({"error": error, "message": message}), 400
    
@cleaner_bp.get("/list")
@jwt_required
@roles_required("end_user")
def list_cleaners():
    """Browse a list of cleaners (end-user)."""
    return jsonify(CleanerProfileService.list_cleaners()), 200
