from typing import Dict, Any, List
from decimal import Decimal, InvalidOperation
from datetime import datetime, time as time_type

from app.models import db, CleanerProfile, CleanerAvailability, ServiceType, User, UserProfile, UserRole
from app.services.cleaner_eligibility import has_booking_conflict, schedule_fits_availability


class CleanerProfileService:
    MAX_YEARS_EXPERIENCE = 100

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
            if years > CleanerProfileService.MAX_YEARS_EXPERIENCE:
                raise ValueError("invalid_years_experience|years_experience must be <= 100.")
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

    @staticmethod
    def list_cleaners(
        service_type=None,
        preferred_date=None,
        preferred_time_start=None,
        preferred_time_end=None,
        exclude_job_request_id=None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Return a list of cleaners with basic information for end-users to browse."""
        service_type_enum = None
        if service_type:
            try:
                service_type_enum = ServiceType(service_type)
            except Exception:
                valid = ", ".join([s.value for s in ServiceType])
                raise ValueError(f"invalid_service_type|service_type must be one of: {valid}.")

        parsed_date = None
        if preferred_date:
            try:
                parsed_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                raise ValueError("invalid_date|preferred_date must be in YYYY-MM-DD format.")

        parsed_start = CleanerProfileService._parse_optional_time(
            preferred_time_start,
            "preferred_time_start",
        )
        parsed_end = CleanerProfileService._parse_optional_time(
            preferred_time_end,
            "preferred_time_end",
        )
        if parsed_start and parsed_end and parsed_end <= parsed_start:
            raise ValueError("invalid_time|preferred_time_end must be strictly after preferred_time_start.")

        excluded_id = None
        if exclude_job_request_id not in (None, ""):
            try:
                excluded_id = int(exclude_job_request_id)
            except (ValueError, TypeError):
                raise ValueError("invalid_request|exclude_job_request_id must be an integer.")

        query = (
            db.session.query(User, UserProfile, CleanerProfile)
            .join(UserProfile, UserProfile.user_id == User.id)
            .join(CleanerProfile, CleanerProfile.user_id == User.id)
            .filter(User.role == UserRole.cleaner, User.is_banned.is_(False))
        )

        if service_type_enum is not None:
            query = query.filter(CleanerProfile.service_type == service_type_enum)

        rows = query.order_by(UserProfile.first_name.asc(), UserProfile.last_name.asc()).all()

        cleaners: List[Dict[str, Any]] = []
        for user, profile, cleaner_profile in rows:
            if parsed_date is not None:
                if not schedule_fits_availability(
                    parsed_date,
                    parsed_start,
                    parsed_end,
                    cleaner_profile.availability,
                ):
                    continue
                if has_booking_conflict(
                    user.id,
                    parsed_date,
                    parsed_start,
                    parsed_end,
                    exclude_job_request_id=excluded_id,
                ):
                    continue

            cleaners.append(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "city": profile.city,
                    "cleaner_profile": cleaner_profile.to_dict(),
                }
            )

        return {"cleaners": cleaners}

    @staticmethod
    def _parse_optional_time(value, field_name):
        if value in (None, ""):
            return None
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).time()
            except (ValueError, TypeError):
                continue
        raise ValueError(f"invalid_time|{field_name} must be in HH:MM format.")

    @staticmethod
    def get_availability(user_id: int) -> Dict[str, Any]:
        profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return {"availability": []}
        slots = (
            CleanerAvailability.query
            .filter_by(cleaner_profile_id=profile.id)
            .order_by(CleanerAvailability.start_date.asc(), CleanerAvailability.start_time.asc())
            .all()
        )
        return {"availability": [a.to_dict() for a in slots]}

    @staticmethod
    def add_availability(user_id: int, data: dict) -> Dict[str, Any]:
        profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise ValueError("not_found|Cleaner profile not found. Please set up your profile first.")

        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        start_time_str = data.get("start_time") or None
        end_time_str = data.get("end_time") or None

        if not start_date_str:
            raise ValueError("invalid_request|start_date is required.")
        if not end_date_str:
            raise ValueError("invalid_request|end_date is required.")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError("invalid_date|start_date must be in YYYY-MM-DD format.")

        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError("invalid_date|end_date must be in YYYY-MM-DD format.")

        if end_date < start_date:
            raise ValueError("invalid_date|end_date must be on or after start_date.")

        start_time = None
        end_time = None

        if start_time_str:
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|start_time must be in HH:MM format.")

        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|end_time must be in HH:MM format.")

        if end_time and not start_time:
            raise ValueError("invalid_time|start_time is required when end_time is set.")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("invalid_time|end_time must be after start_time.")

        # Check for overlap with existing slots
        for existing in profile.availability:
            if CleanerProfileService._slots_overlap(existing, start_date, end_date, start_time, end_time):
                raise ValueError(
                    "invalid_request|This slot overlaps with an existing availability slot."
                )

        slot = CleanerAvailability(
            cleaner_profile_id=profile.id,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
        )
        db.session.add(slot)
        db.session.commit()
        return {"message": "Availability slot added.", "availability": slot.to_dict()}

    @staticmethod
    def _slots_overlap(existing, new_start_date, new_end_date, new_start_time, new_end_time) -> bool:
        """Return True if the new slot's date/time range overlaps with an existing slot."""
        # No date overlap - no conflict
        if new_start_date > existing.end_date or existing.start_date > new_end_date:
            return False

        # Dates overlap. If either slot has no time restriction it covers the whole day.
        if existing.start_time is None or new_start_time is None:
            return True

        # Both have times - check time range overlap.
        # Treat a missing end_time as end of day.
        _END_OF_DAY = time_type(23, 59, 59)
        existing_end = existing.end_time or _END_OF_DAY
        new_end = new_end_time or _END_OF_DAY

        return new_start_time < existing_end and existing.start_time < new_end

    @staticmethod
    def update_availability(user_id: int, availability_id: int, data: dict) -> Dict[str, Any]:
        profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise ValueError("not_found|Cleaner profile not found.")

        slot = CleanerAvailability.query.filter_by(
            id=availability_id, cleaner_profile_id=profile.id
        ).first()
        if not slot:
            raise ValueError("not_found|Availability slot not found.")

        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        start_time_str = data.get("start_time") or None
        end_time_str = data.get("end_time") or None

        if not start_date_str:
            raise ValueError("invalid_request|start_date is required.")
        if not end_date_str:
            raise ValueError("invalid_request|end_date is required.")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError("invalid_date|start_date must be in YYYY-MM-DD format.")

        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError("invalid_date|end_date must be in YYYY-MM-DD format.")

        if end_date < start_date:
            raise ValueError("invalid_date|end_date must be on or after start_date.")

        start_time = None
        end_time = None

        if start_time_str:
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|start_time must be in HH:MM format.")

        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|end_time must be in HH:MM format.")

        if end_time and not start_time:
            raise ValueError("invalid_time|start_time is required when end_time is set.")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("invalid_time|end_time must be after start_time.")

        # Check for overlap with other slots (exclude the one being edited)
        for existing in profile.availability:
            if existing.id == availability_id:
                continue
            if CleanerProfileService._slots_overlap(existing, start_date, end_date, start_time, end_time):
                raise ValueError(
                    "invalid_request|This slot overlaps with an existing availability slot."
                )

        slot.start_date = start_date
        slot.end_date = end_date
        slot.start_time = start_time
        slot.end_time = end_time
        db.session.commit()
        return {"message": "Availability slot updated.", "availability": slot.to_dict()}

    @staticmethod
    def delete_availability(user_id: int, availability_id: int) -> Dict[str, Any]:
        profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise ValueError("not_found|Cleaner profile not found.")

        slot = CleanerAvailability.query.filter_by(
            id=availability_id, cleaner_profile_id=profile.id
        ).first()
        if not slot:
            raise ValueError("not_found|Availability slot not found.")

        db.session.delete(slot)
        db.session.commit()
        return {"message": "Availability slot removed."}
