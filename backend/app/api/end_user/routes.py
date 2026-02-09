from flask import Blueprint, jsonify, g
from app.api.auth.decorators import jwt_required, roles_required

end_user_bp = Blueprint("end_user", __name__)

@end_user_bp.before_request
@jwt_required
@roles_required("end_user")
def _guard():
    pass

@end_user_bp.get("/dashboard")
def dashboard():
    return jsonify(message=f"Welcome end-user {g.user['email']}")
