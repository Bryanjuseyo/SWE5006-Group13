from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from jwt import ExpiredSignatureError, InvalidTokenError

from app.models import db, User
from app.services.auth_service import AuthService
from app.services.two_factor_service import TwoFactorService
from app.services.email_service import EmailService
from app.services.jwt_service import generate_token, decode_2fa_temp_token
from app.api.auth.decorators import jwt_required

auth_bp = Blueprint("auth", __name__)


def _parse_error(e: ValueError):
    raw = str(e)
    if "|" in raw:
        error, message = raw.split("|", 1)
    else:
        error, message = "bad_request", raw
    return error, message


# =============================================
# REGISTER / LOGIN
# =============================================

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    try:
        result = AuthService.register_user(
            email=data.get("email"),
            password=data.get("password"),
            role_raw=data.get("role"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            address=data.get("address"),
            city=data.get("city"),
            service_type=data.get("service_type"),
            hourly_rate=data.get("hourly_rate"),
            years_experience=data.get("years_experience"),
        )
        return jsonify(result), 201

    except ValueError as e:
        error, message = _parse_error(e)
        status = 409 if error == "duplicate_email" else 400
        return jsonify({"error": error, "message": message}), status


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    try:
        result = AuthService.login_user(
            email=data.get("email"),
            password=data.get("password"),
        )
        return jsonify(result), 200

    except ValueError as e:
        error, message = _parse_error(e)
        if error == "locked":
            return jsonify({"error": error, "message": message}), 423
        return jsonify({"error": error, "message": message}), 401


# =============================================
# TWO-FACTOR AUTHENTICATION
# =============================================

@auth_bp.get("/2fa/status")
@jwt_required
def two_fa_status():
    """Return the current user's 2FA enabled status."""
    user = User.query.get(g.user["user_id"])
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404
    return jsonify({"two_factor_enabled": user.two_factor_enabled}), 200


@auth_bp.post("/2fa/setup")
@jwt_required
def two_fa_setup():
    """Generate and email an OTP to begin 2FA setup."""
    user = User.query.get(g.user["user_id"])
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404

    otp = TwoFactorService.generate_and_store_otp(user)
    EmailService.send_otp_email(user.email, otp, "2FA setup")
    return jsonify({"message": "OTP sent to your email address."}), 200


@auth_bp.post("/2fa/enable")
@jwt_required
def two_fa_enable():
    """Verify the setup OTP and enable 2FA for the account."""
    data = request.get_json(silent=True) or {}
    otp = (data.get("otp") or "").strip()

    user = User.query.get(g.user["user_id"])
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404

    try:
        TwoFactorService.verify_otp(user, otp)
    except ValueError as e:
        error, message = _parse_error(e)
        return jsonify({"error": error, "message": message}), 400

    user.two_factor_enabled = True
    user.two_factor_otp = None
    user.two_factor_otp_expires = None
    db.session.commit()
    return jsonify({"message": "Two-factor authentication has been enabled."}), 200


@auth_bp.post("/2fa/disable")
@jwt_required
def two_fa_disable():
    """Verify password and disable 2FA for the account."""
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""

    user = User.query.get(g.user["user_id"])
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404
    if not user.two_factor_enabled:
        return jsonify({"error": "not_enabled", "message": "2FA is not enabled."}), 400
    if not user.check_password(password):
        return jsonify({"error": "invalid_password", "message": "Incorrect password."}), 401

    user.two_factor_enabled = False
    user.two_factor_otp = None
    user.two_factor_otp_expires = None
    db.session.commit()
    return jsonify({"message": "Two-factor authentication has been disabled."}), 200


@auth_bp.post("/2fa/resend")
def two_fa_resend():
    """Resend a login OTP using the existing temp_token, and return a fresh temp_token."""
    data = request.get_json(silent=True) or {}
    temp_token = (data.get("temp_token") or "").strip()

    try:
        payload = decode_2fa_temp_token(temp_token)
    except (ExpiredSignatureError, InvalidTokenError, Exception):
        return jsonify({"error": "invalid_token", "message": "Invalid or expired session. Please log in again."}), 401

    user = User.query.get(payload.get("user_id"))
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404

    from app.services.jwt_service import generate_2fa_temp_token
    otp = TwoFactorService.generate_and_store_otp(user)
    EmailService.send_otp_email(user.email, otp, "login verification")
    new_temp_token = generate_2fa_temp_token(user.id)

    return jsonify({
        "message": "A new verification code has been sent to your email.",
        "temp_token": new_temp_token,
    }), 200


@auth_bp.post("/2fa/verify")
def two_fa_verify():
    """Verify the login OTP (from temp_token) and return a full JWT."""
    data = request.get_json(silent=True) or {}
    otp = (data.get("otp") or "").strip()
    temp_token = (data.get("temp_token") or "").strip()

    try:
        payload = decode_2fa_temp_token(temp_token)
    except (ExpiredSignatureError, InvalidTokenError, Exception):
        return jsonify({"error": "invalid_token", "message": "Invalid or expired session. Please log in again."}), 401

    user = User.query.get(payload.get("user_id"))
    if not user:
        return jsonify({"error": "not_found", "message": "User not found."}), 404

    try:
        TwoFactorService.verify_otp(user, otp)
    except ValueError as e:
        error, message = _parse_error(e)
        return jsonify({"error": error, "message": message}), 401

    # Clear OTP, record login time, and ensure 2FA is marked as enabled
    user.two_factor_otp = None
    user.two_factor_otp_expires = None
    user.two_factor_enabled = True
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    token = generate_token(user.id, user.email, user.role.value)
    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": user.to_dict(),
    }), 200
