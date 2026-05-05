from flask import Blueprint, request, jsonify, g
from jwt import ExpiredSignatureError, InvalidTokenError
from app.services.cleaner_profile_service import CleanerProfileService
from app.services.job_request_service import JobRequestService
from app.api.auth.decorators import jwt_required, roles_required
from app.services.jwt_service import decode_token

cleaner_bp = Blueprint("cleaner", __name__)


def _handle_error(e):
    raw = str(e)
    error, message = raw.split("|", 1) if "|" in raw else ("bad_request", raw)
    status_codes = {
        "not_found": 404,
        "forbidden": 403,
        "invalid_request": 400,
        "invalid_date": 400,
        "invalid_service_type": 400,
        "invalid_time": 400,
    }
    return jsonify({"error": error, "message": message}), status_codes.get(error, 400)


def _parse_pagination_args():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=25, type=int)
    if page is None or per_page is None:
        raise ValueError("invalid_pagination|page and per_page must be integers.")
    return page, per_page


@cleaner_bp.before_request
def _guard():
    # Let CORS preflight through before touching auth headers
    if request.method == "OPTIONS":
        return None

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
        return _handle_error(e)


@cleaner_bp.get("/list")
@jwt_required
@roles_required("end_user")
def list_cleaners():
    """Browse a list of cleaners (end-user)."""
    try:
        return jsonify(CleanerProfileService.list_cleaners(
            service_type=request.args.get("service_type"),
            preferred_date=request.args.get("preferred_date"),
            preferred_time_start=request.args.get("preferred_time_start"),
            preferred_time_end=request.args.get("preferred_time_end"),
            exclude_job_request_id=request.args.get("exclude_job_request_id"),
        )), 200
    except ValueError as e:
        return _handle_error(e)


@cleaner_bp.get("/availability")
@jwt_required
@roles_required("cleaner")
def get_availability():
    """Return all availability slots for the authenticated cleaner."""
    user_id = g.user["user_id"]
    return jsonify(CleanerProfileService.get_availability(user_id)), 200


@cleaner_bp.post("/availability")
@jwt_required
@roles_required("cleaner")
def add_availability():
    """Add a new availability slot."""
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(CleanerProfileService.add_availability(user_id, data)), 201
    except ValueError as e:
        return _handle_error(e)


@cleaner_bp.put("/availability/<int:availability_id>")
@jwt_required
@roles_required("cleaner")
def update_availability(availability_id):
    """Update an existing availability slot."""
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(CleanerProfileService.update_availability(user_id, availability_id, data)), 200
    except ValueError as e:
        return _handle_error(e)


@cleaner_bp.delete("/availability/<int:availability_id>")
@jwt_required
@roles_required("cleaner")
def delete_availability(availability_id):
    """Remove an availability slot."""
    user_id = g.user["user_id"]
    try:
        return jsonify(CleanerProfileService.delete_availability(user_id, availability_id)), 200
    except ValueError as e:
        return _handle_error(e)


@cleaner_bp.get("/schedule")
@jwt_required
@roles_required("cleaner")
def get_schedule():
    """Return upcoming confirmed/in_progress jobs for the cleaner."""
    user_id = g.user["user_id"]
    try:
        page, per_page = _parse_pagination_args()
        return jsonify(JobRequestService.get_cleaner_schedule(user_id, page, per_page)), 200
    except ValueError as e:
        return _handle_error(e)


@cleaner_bp.get("/available-jobs")
@jwt_required
@roles_required("cleaner")
def get_available_jobs():
    """Return open (unassigned, pending) jobs matching the cleaner's service type."""
    user_id = g.user["user_id"]
    try:
        page, per_page = _parse_pagination_args()
        return jsonify(JobRequestService.get_available_jobs(user_id, page, per_page)), 200
    except ValueError as e:
        return _handle_error(e)
