from flask import Blueprint, jsonify, g
from app.api.auth.decorators import jwt_required, roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
@jwt_required
@roles_required("administrator")
def _guard():
    pass


@admin_bp.get("/dashboard")
def dashboard():
    return jsonify(message=f"Welcome admin {g.user['email']}")
