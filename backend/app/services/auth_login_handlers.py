from datetime import datetime, timedelta, timezone

from app.models import db, User
from app.services.email_service import EmailService
from app.services.two_factor_service import TwoFactorService
from app.services.jwt_service import generate_token, generate_2fa_temp_token


LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 15


class LoginContext:
    def __init__(self, email: str, password: str):
        self.email = (email or "").strip().lower()
        self.password = password or ""
        self.user = None


class LoginHandler:
    def __init__(self, next_handler=None):
        self.next_handler = next_handler

    def handle(self, context: LoginContext):
        if self.next_handler:
            return self.next_handler.handle(context)
        return None


class RequiredCredentialsHandler(LoginHandler):
    def handle(self, context: LoginContext):
        if not context.email or not context.password:
            raise ValueError("invalid_credentials|Email and password are required.")
        return super().handle(context)


class UserExistsHandler(LoginHandler):
    def handle(self, context: LoginContext):
        user = User.query.filter_by(email=context.email).first()
        if not user:
            raise ValueError("invalid_credentials|Invalid email or password.")
        context.user = user
        return super().handle(context)


class BannedUserHandler(LoginHandler):
    def handle(self, context: LoginContext):
        if context.user.is_banned:
            raise ValueError("banned|Your account has been banned. Contact support for assistance.")
        return super().handle(context)


class LockedUserHandler(LoginHandler):
    def handle(self, context: LoginContext):
        now = datetime.now(timezone.utc)
        if context.user.locked_until and context.user.locked_until > now:
            raise ValueError("locked|Too many failed attempts. Try again later.")
        return super().handle(context)


class PasswordCheckHandler(LoginHandler):
    def handle(self, context: LoginContext):
        now = datetime.now(timezone.utc)
        user = context.user

        if not user.check_password(context.password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)

            db.session.commit()
            raise ValueError("invalid_credentials|Invalid email or password.")

        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        return super().handle(context)


class TwoFactorLoginHandler(LoginHandler):
    def handle(self, context: LoginContext):
        from flask import current_app

        user = context.user

        if current_app.config.get("SKIP_2FA"):
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            token = generate_token(user.id, user.email, user.role.value)
            return {
                "token": token,
                "user": user.to_dict()
            }

        otp = TwoFactorService.generate_and_store_otp(user)
        EmailService.send_otp_email(user.email, otp, "login verification")
        temp_token = generate_2fa_temp_token(user.id)

        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "OTP sent to your email. Please enter it to complete login."
        }
