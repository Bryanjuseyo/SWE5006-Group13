from flask import Blueprint, jsonify, g
from app.api.auth.decorators import jwt_required, roles_required

cleaner_bp = Blueprint("cleaner", __name__)

@cleaner_bp.before_request
@jwt_required
@roles_required("cleaner")
def _guard():
    pass

@cleaner_bp.get("/dashboard")
def dashboard():
    return jsonify(message=f"Welcome cleaner {g.user['email']}")
