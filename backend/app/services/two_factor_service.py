import secrets
from datetime import datetime, timedelta, timezone

from app.models import db, User, bcrypt

OTP_EXPIRY_MINUTES = 5


class TwoFactorService:

    @staticmethod
    def generate_and_store_otp(user: User) -> str:
        """Generate a 6-digit OTP, hash and store it, return the raw OTP."""
        otp = f"{secrets.randbelow(1_000_000):06d}"
        user.two_factor_otp = bcrypt.generate_password_hash(otp).decode("utf-8")
        user.two_factor_otp_expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
        db.session.commit()
        return otp

    @staticmethod
    def verify_otp(user: User, otp: str) -> None:
        """
        Verify the OTP against the stored hash and expiry.
        Raises ValueError on failure.
        """
        if not otp:
            raise ValueError("invalid_otp|OTP is required.")
        if not user.two_factor_otp or not user.two_factor_otp_expires:
            raise ValueError("invalid_otp|No OTP has been requested. Please request a new one.")

        now = datetime.now(timezone.utc)
        expires = user.two_factor_otp_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            raise ValueError("expired_otp|OTP has expired. Please request a new one.")

        if not bcrypt.check_password_hash(user.two_factor_otp, otp):
            raise ValueError("invalid_otp|Incorrect OTP. Please try again.")
