import re
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone

from app.models import db, User, UserRole, UserProfile, CleanerProfile, ServiceType
from app.services.jwt_service import generate_token, generate_2fa_temp_token
from app.services.two_factor_service import TwoFactorService
from app.services.email_service import EmailService

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[89]\d{7}$")
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
    def register_user(email: str, password: str, role_raw: str,
                      first_name: str = None, last_name: str = None,
                      phone: str = None, address: str = None, city: str = None,
                      service_type: str = None, hourly_rate=None,
                      years_experience: int = None) -> Dict[str, Any]:
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

        # Profile fields are mandatory
        if not first_name or not first_name.strip():
            raise ValueError("invalid_profile|First name is required.")
        if not last_name or not last_name.strip():
            raise ValueError("invalid_profile|Last name is required.")

        if phone and not PHONE_RE.match(phone):
            raise ValueError("invalid_phone|Phone number must start with 8 or 9 and be 8 digits long.")

        # Cleaner-specific validation
        if role == UserRole.cleaner:
            if not service_type:
                raise ValueError("invalid_cleaner_profile|Service type is required for cleaners.")
            try:
                service_type_enum = ServiceType(service_type)
            except Exception:
                valid = ", ".join([s.value for s in ServiceType])
                raise ValueError(f"invalid_service_type|service_type must be one of: {valid}.")

        # duplicate check (fast path)
        if User.query.filter_by(email=email).first():
            raise ValueError("duplicate_email|Email is already registered.")

        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.flush()  # get user.id without committing

            # Create user profile
            profile = UserProfile(
                user_id=user.id,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone=phone or None,
                address=address.strip() if address else None,
                city=city.strip() if city else None,
            )
            db.session.add(profile)

            # Create cleaner profile if role is cleaner
            if role == UserRole.cleaner:
                cleaner_profile = CleanerProfile(
                    user_id=user.id,
                    service_type=service_type_enum,
                    hourly_rate=hourly_rate if hourly_rate is not None else None,
                    years_experience=int(years_experience) if years_experience is not None else 0,
                )
                db.session.add(cleaner_profile)

            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("duplicate_email|Email is already registered.")

        otp = TwoFactorService.generate_and_store_otp(user)
        EmailService.send_otp_email(user.email, otp, "registration verification")
        temp_token = generate_2fa_temp_token(user.id)

        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "Account created. A verification code has been sent to your email.",
        }

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

        # Check if user is banned
        if user.is_banned:
            raise ValueError("banned|Your account has been banned. Contact support for assistance.")

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

        # Success — reset lockout state
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        # Skip 2FA for testing
        from flask import current_app
        if current_app.config.get("SKIP_2FA"):
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            token = generate_token(user.id, user.email, user.role.value)
            return {"token": token, "user": user.to_dict()}

        # Always require OTP verification. For existing users who predate 2FA,
        # two_factor_enabled may be False — we still send the OTP and will set
        # it to True once they verify, bringing them onto the 2FA flow.
        otp = TwoFactorService.generate_and_store_otp(user)
        EmailService.send_otp_email(user.email, otp, "login verification")
        temp_token = generate_2fa_temp_token(user.id)
        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "OTP sent to your email. Please enter it to complete login.",
        }
