import re
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError

from app.models import db, User, UserRole, UserProfile, CleanerProfile, ServiceType
from app.services.jwt_service import generate_2fa_temp_token
from app.services.two_factor_service import TwoFactorService
from app.services.email_service import EmailService

from app.services.auth_login_handlers import (
    LoginContext,
    RequiredCredentialsHandler,
    UserExistsHandler,
    BannedUserHandler,
    LockedUserHandler,
    PasswordCheckHandler,
    TwoFactorLoginHandler,
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[89]\d{7}$")
LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 15
MAX_YEARS_EXPERIENCE = 100


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
            if years_experience is not None:
                try:
                    years_experience = int(years_experience)
                except (ValueError, TypeError):
                    raise ValueError("invalid_years_experience|years_experience must be an integer.")
                if years_experience < 0:
                    raise ValueError("invalid_years_experience|years_experience must be >= 0.")
                if years_experience > MAX_YEARS_EXPERIENCE:
                    raise ValueError("invalid_years_experience|years_experience must be <= 100.")

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
                    years_experience=years_experience if years_experience is not None else 0,
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
    @staticmethod
    def login_user(email: str, password: str):
        context = LoginContext(email, password)

        chain = RequiredCredentialsHandler(
            UserExistsHandler(
                BannedUserHandler(
                    LockedUserHandler(
                        PasswordCheckHandler(
                            TwoFactorLoginHandler()
                        )
                    )
                )
            )
        )

        return chain.handle(context)
