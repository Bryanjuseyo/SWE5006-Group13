from flask import Blueprint, jsonify, request, g
from app.api.auth.decorators import jwt_required, roles_required
from app.services.admin_service import AdminService

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def _guard():
    if request.method == "OPTIONS":
        return
    return _auth_guard()


@jwt_required
@roles_required("administrator")
def _auth_guard():
    pass


def _parse_pagination_args():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=25, type=int)
    if page is None or per_page is None:
        raise ValueError("invalid_pagination|page and per_page must be integers.")
    return page, per_page


@admin_bp.get("/dashboard")
def dashboard():
    return jsonify(message=f"Welcome admin {g.user['email']}")


@admin_bp.get("/stats")
def stats():
    data = AdminService.get_dashboard_stats()
    return jsonify(data)


@admin_bp.get("/users")
def get_users():
    role_filter = request.args.get("role")
    banned_filter = request.args.get("banned")
    search = request.args.get("search")
    try:
        page, per_page = _parse_pagination_args()
        data = AdminService.get_all_users(
            role_filter=role_filter,
            banned_filter=banned_filter,
            search=search,
            page=page,
            per_page=per_page,
        )
        return jsonify(data)
    except ValueError as e:
        code, msg = str(e).split("|", 1)
        return jsonify({"error": code, "message": msg}), 400


@admin_bp.patch("/users/<int:user_id>/ban")
def ban_user(user_id):
    body = request.get_json(silent=True) or {}
    reason = body.get("reason")
    try:
        data = AdminService.ban_user(user_id, reason=reason)
        return jsonify(data)
    except ValueError as e:
        parts = str(e).split("|", 1)
        code = parts[0]
        msg = parts[1] if len(parts) > 1 else str(e)
        status = 404 if code == "not_found" else 400
        return jsonify({"error": code, "message": msg}), status


@admin_bp.patch("/users/<int:user_id>/unban")
def unban_user(user_id):
    try:
        data = AdminService.unban_user(user_id)
        return jsonify(data)
    except ValueError as e:
        parts = str(e).split("|", 1)
        code = parts[0]
        msg = parts[1] if len(parts) > 1 else str(e)
        status = 404 if code == "not_found" else 400
        return jsonify({"error": code, "message": msg}), status


@admin_bp.get("/bookings")
def get_bookings():
    status_filter = request.args.get("status")
    search = request.args.get("search")
    try:
        page, per_page = _parse_pagination_args()
        data = AdminService.get_all_bookings(
            status_filter=status_filter,
            search=search,
            page=page,
            per_page=per_page,
        )
        return jsonify(data)
    except ValueError as e:
        code, msg = str(e).split("|", 1)
        return jsonify({"error": code, "message": msg}), 400


@admin_bp.patch("/bookings/<int:job_request_id>/reject")
def reject_booking(job_request_id):
    body = request.get_json(silent=True) or {}
    reason = body.get("reason")
    try:
        data = AdminService.reject_booking(job_request_id, reason=reason)
        return jsonify(data)
    except ValueError as e:
        parts = str(e).split("|", 1)
        code = parts[0]
        msg = parts[1] if len(parts) > 1 else str(e)
        status = 404 if code == "not_found" else 400
        return jsonify({"error": code, "message": msg}), status
