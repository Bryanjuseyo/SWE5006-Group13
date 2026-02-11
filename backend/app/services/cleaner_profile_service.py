from typing import Dict, Any
from decimal import Decimal, InvalidOperation

from app.models import db, CleanerProfile, ServiceType


class CleanerProfileService:
    @staticmethod
    def get_cleaner_profile(user_id: int) -> Dict[str, Any]:
        profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        return {"profile": profile.to_dict() if profile else None}

    @staticmethod
    def upsert_cleaner_profile(user_id: int, data: dict) -> Dict[str, Any]:
        data = data or {}

        # Allowed fields
        allowed = {"service_type", "hourly_rate", "years_experience"}
        updates = {k: data.get(k) for k in allowed if k in data}

        # Validate service_type if provided
        if "service_type" in updates:
            try:
                updates["service_type"] = ServiceType(updates["service_type"])
            except Exception:
                valid = ", ".join([s.value for s in ServiceType])
                raise ValueError(f"invalid_service_type|service_type must be one of: {valid}.")

        # Validate hourly_rate if provided
        if "hourly_rate" in updates and updates["hourly_rate"] is not None:
            try:
                rate = Decimal(str(updates["hourly_rate"]))
            except (InvalidOperation, ValueError):
                raise ValueError("invalid_hourly_rate|hourly_rate must be a number.")
            if rate < 0:
                raise ValueError("invalid_hourly_rate|hourly_rate must be >= 0.")
            updates["hourly_rate"] = rate

        # Validate years_experience if provided
        if "years_experience" in updates and updates["years_experience"] is not None:
            try:
                years = int(updates["years_experience"])
            except (ValueError, TypeError):
                raise ValueError("invalid_years_experience|years_experience must be an integer.")
            if years < 0:
                raise ValueError("invalid_years_experience|years_experience must be >= 0.")
            updates["years_experience"] = years

        profile = CleanerProfile.query.filter_by(user_id=user_id).first()

        if profile is None:
            if "service_type" not in updates:
                raise ValueError("invalid_profile|service_type is required.")
            profile = CleanerProfile(user_id=user_id, **updates)
            db.session.add(profile)
        else:
            for k, v in updates.items():
                setattr(profile, k, v)

        db.session.commit()
        return {"message": "Cleaner profile updated.", "profile": profile.to_dict()}
