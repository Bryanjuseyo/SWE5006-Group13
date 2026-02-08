import re
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone

from app.models import db, User, UserRole
from app.services.jwt_service import generate_token

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 15

class AuthService:

    # =============================================
    # REGISTER USER
    # =============================================
    @staticmethod
    def _password_is_valid(pw: str) -> bool:
        if not pw or len(pw) < 8:
            return False
        return any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw)

    @staticmethod
    def register_user(email: str, password: str, role_raw: str) -> Dict[str, Any]:
        email = (email or "").strip().lower()
        password = password or ""
        role_raw = (role_raw or "").strip()

        # validations (raise ValueError with structured info)
        if not EMAIL_RE.match(email):
            raise ValueError("invalid_email|Invalid email format.")

        if not AuthService._password_is_valid(password):
            raise ValueError("invalid_password|Password must be at least 8 characters and contain letters and numbers.")

        try:
            role = UserRole(role_raw)
        except Exception:
            valid = ", ".join([r.value for r in UserRole])
            raise ValueError(f"invalid_role|Role must be one of: {valid}.")

        # duplicate check (fast path)
        if User.query.filter_by(email=email).first():
            raise ValueError("duplicate_email|Email is already registered.")

        user = User(email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # handles race condition where two register requests hit at same time
            raise ValueError("duplicate_email|Email is already registered.")

        return {"message": "Registration successful.", "user": user.to_dict()}

    # =============================================
    # LOGIN USER
    # =============================================
    def login_user(email: str, password: str):
        email = (email or "").strip().lower()
        password = password or ""

        if not email or not password:
            raise ValueError("invalid_credentials|Email and password are required.")

        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("invalid_credentials|Invalid email or password.")

        now = datetime.now(timezone.utc)

        # Check user locked
        if user.locked_until and user.locked_until > now:
            raise ValueError("locked|Too many failed attempts. Try again later.")

        # Check Password
        if not user.check_password(password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)

            db.session.commit()
            raise ValueError("invalid_credentials|Invalid email or password.")

        # Success
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        db.session.commit()

        token = generate_token(user.id, user.email, user.role.value)

        return {
            "message": "Login successful.",
            "token": token,
            "user": user.to_dict(),
        }