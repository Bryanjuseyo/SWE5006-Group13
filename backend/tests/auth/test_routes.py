from flask import Blueprint, jsonify, g
from app.api.auth.decorators import jwt_required


def register_auth_test_routes(app):
    """
    Register test-only auth routes ONCE at app startup.
    Keep this file close to auth tests so conftest.py stays clean.
    """
    bp = Blueprint("auth_test_routes", __name__)

    @bp.get("/api/_jwt_missing_bearer")
    @jwt_required
    def _jwt_missing_bearer():
        return jsonify(ok=True), 200

    @bp.get("/api/_jwt_non_bearer")
    @jwt_required
    def _jwt_non_bearer():
        return jsonify(ok=True), 200

    @bp.get("/api/_jwt_expired")
    @jwt_required
    def _jwt_expired():
        return jsonify(ok=True), 200

    @bp.get("/api/_jwt_invalid")
    @jwt_required
    def _jwt_invalid():
        return jsonify(ok=True), 200

    @bp.get("/api/_jwt_success")
    @jwt_required
    def _jwt_success():
        return jsonify(g_user=g.user), 200

    app.register_blueprint(bp)
