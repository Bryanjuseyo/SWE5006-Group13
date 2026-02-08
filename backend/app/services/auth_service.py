import re
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError

from app.models import db, User, UserRole

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class AuthService:
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
