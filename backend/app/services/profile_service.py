import re
from typing import Dict, Any
from app.models import db, User, UserProfile

PHONE_RE = re.compile(r"^[89]\d{7}$")

class ProfileService:
    @staticmethod
    def get_profile(user_id: int) -> Dict[str, Any]:
        user = User.query.get(user_id)
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        return {
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
            "profile": profile.to_dict() if profile else None,
        }

    @staticmethod
    def upsert_profile(user_id: int, data: dict) -> Dict[str, Any]:
        allowed = {"first_name", "last_name", "phone", "address", "city"}
        updates = {k: v for k, v in (data or {}).items() if k in allowed}

        phone = updates.get("phone")
        if phone is not None and not PHONE_RE.match(phone):
            raise ValueError(
                "invalid_phone|Phone number must start with 8 or 9 and be 8 digits long."
            )

        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if profile is None:
            if not updates.get("first_name") or not updates.get("last_name"):
                raise ValueError(
                    "invalid_profile|first_name and last_name are required."
                )
            profile = UserProfile(user_id=user_id, **updates)
            db.session.add(profile)
        else:
            for k, v in updates.items():
                setattr(profile, k, v)

        db.session.commit()
        return {"message": "Profile updated.", "profile": profile.to_dict()}
