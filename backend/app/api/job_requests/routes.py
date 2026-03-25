from flask import Blueprint, request, jsonify, g
from app.api.auth.decorators import jwt_required, roles_required
from app.services.job_request_service import JobRequestService
from app.services.matching_service import MatchingService

job_requests_bp = Blueprint("job_requests", __name__)


def _handle_error(e):
    """Parse ValueError and return appropriate HTTP response."""
    raw = str(e)
    if "|" in raw:
        error, message = raw.split("|", 1)
    else:
        error, message = "bad_request", raw

    # Map error codes to HTTP status codes
    status_codes = {
        "not_found": 404,
        "forbidden": 403,
        "invalid_status": 400,
        "invalid_request": 400,
        "invalid_service_type": 400,
        "invalid_date": 400,
        "invalid_time": 400,
    }
    status = status_codes.get(error, 400)
    return jsonify({"error": error, "message": message}), status


# =============================================
# JOB REQUEST CRUD ENDPOINTS
# =============================================


@job_requests_bp.post("/")
@jwt_required
@roles_required("end_user")
def create_job_request():
    """
    Create a new job request.
    """
    user_id = g.user["user_id"]
    data = request.get_json(silent=True) or {}

    try:
        result = JobRequestService.create_job_request(user_id, data)
        return jsonify(result), 201
    except ValueError as e:
        return _handle_error(e)


@job_requests_bp.get("/")
@jwt_required
@roles_required("end_user", "cleaner", "administrator")
def list_job_requests():
    """
    View job requests based on user role and optional status filter.
    """
    user_id = g.user["user_id"]
    role = g.user["role"]
    status = request.args.get("status")

    try:
        result = JobRequestService.get_job_requests(user_id, role, status)
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


@job_requests_bp.get("/<int:job_request_id>")
@jwt_required
@roles_required("end_user", "cleaner", "administrator")
def get_job_request(job_request_id):
    """
    Get a single job request by ID.
    """
    user_id = g.user["user_id"]
    role = g.user["role"]

    try:
        result = JobRequestService.get_job_request(job_request_id, user_id, role)
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


@job_requests_bp.put("/<int:job_request_id>")
@jwt_required
@roles_required("end_user")
def update_job_request(job_request_id):
    """
    Update job request details.
    """
    user_id = g.user["user_id"]
    role = g.user["role"]
    data = request.get_json(silent=True) or {}

    try:
        result = JobRequestService.update_job_request(
            job_request_id, user_id, role, data
        )
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


@job_requests_bp.delete("/<int:job_request_id>")
@jwt_required
@roles_required("end_user")
def delete_job_request(job_request_id):
    """
    Delete a job request.
    Only the end user who created the request can delete it.
    """
    user_id = g.user["user_id"]
    role = g.user["role"]

    try:
        result = JobRequestService.delete_job_request(job_request_id, user_id, role)
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


# =============================================
# JOB STATUS ENDPOINT
# =============================================


@job_requests_bp.patch("/<int:job_request_id>/status")
@jwt_required
@roles_required("end_user", "cleaner")
def update_job_status(job_request_id):
    """
    Update job request status.
    """
    user_id = g.user["user_id"]
    role = g.user["role"]
    data = request.get_json(silent=True) or {}

    new_status = data.get("status")
    if not new_status:
        return jsonify({
            "error": "invalid_request",
            "message": "status is required."
        }), 400

    try:
        result = JobRequestService.update_job_status(
            job_request_id, user_id, role, new_status
        )
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


# =============================================
# AUTOMATED CLEANER MATCHING
# =============================================


@job_requests_bp.get("/<int:job_request_id>/match")
@jwt_required
@roles_required("end_user", "administrator")
def match_cleaners(job_request_id):
    """Find matching cleaners for a job request."""
    user_id = g.user["user_id"]
    role = g.user["role"]

    try:
        result = MatchingService.find_matching_cleaners(job_request_id, user_id, role)
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)


@job_requests_bp.post("/<int:job_request_id>/auto-assign")
@jwt_required
@roles_required("end_user", "administrator")
def auto_assign_cleaner(job_request_id):
    """Auto-assign the best matching cleaner to a job request."""
    user_id = g.user["user_id"]
    role = g.user["role"]

    try:
        result = MatchingService.auto_assign_cleaner(job_request_id, user_id, role)
        return jsonify(result), 200
    except ValueError as e:
        return _handle_error(e)
