"""
Seed script for JMeter performance testing.

"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app  # noqa: E402
from app.models import db, User, UserRole, UserProfile, CleanerProfile, ServiceType  # noqa: E402

PASSWORD = "Password1"

END_USERS = [
    {
        "email": f"enduser{i}@test.com",
        "first_name": f"EndUser{i}",
        "last_name": "Test",
        "phone": None,
        "address": f"{i} Test Street",
        "city": "Singapore",
    }
    for i in range(1, 51)
]

# Mix of partial and full cleaners with varying rates/experience so the
# matching algorithm has meaningful data to score against.
CLEANERS = [
    {
        "email": f"cleaner{i}@test.com",
        "first_name": f"Cleaner{i}",
        "last_name": "Test",
        "phone": None,
        "address": f"{i} Cleaner Road",
        "city": "Singapore",
        "service_type": "full" if i % 2 == 0 else "partial",
        "hourly_rate": round(15 + (i * 2), 2),   # $17 – $35/hr
        "years_experience": (i % 10) + 1,          # 1 – 10 years
    }
    for i in range(1, 501)
]


def seed():
    app = create_app()
    with app.app_context():
        created_end_users = 0
        skipped_end_users = 0
        created_cleaners = 0
        skipped_cleaners = 0

        # ── End users ────────────────────────────────────────────────────────
        for u in END_USERS:
            if User.query.filter_by(email=u["email"]).first():
                skipped_end_users += 1
                continue

            user = User(
                email=u["email"],
                role=UserRole.end_user,
                two_factor_enabled=False,   # allow direct login in JMeter
            )
            user.set_password(PASSWORD)
            db.session.add(user)
            db.session.flush()  # populate user.id before creating profile

            db.session.add(UserProfile(
                user_id=user.id,
                first_name=u["first_name"],
                last_name=u["last_name"],
                phone=u["phone"],
                address=u["address"],
                city=u["city"],
            ))
            created_end_users += 1

        # ── Cleaners ─────────────────────────────────────────────────────────
        for c in CLEANERS:
            if User.query.filter_by(email=c["email"]).first():
                skipped_cleaners += 1
                continue

            user = User(
                email=c["email"],
                role=UserRole.cleaner,
                two_factor_enabled=False,
            )
            user.set_password(PASSWORD)
            db.session.add(user)
            db.session.flush()

            db.session.add(UserProfile(
                user_id=user.id,
                first_name=c["first_name"],
                last_name=c["last_name"],
                phone=c["phone"],
                address=c["address"],
                city=c["city"],
            ))
            db.session.add(CleanerProfile(
                user_id=user.id,
                service_type=ServiceType(c["service_type"]),
                hourly_rate=c["hourly_rate"],
                years_experience=c["years_experience"],
            ))
            created_cleaners += 1

        db.session.commit()

        print(f"End users  — created: {created_end_users}, skipped (already exist): {skipped_end_users}")
        print(f"Cleaners   — created: {created_cleaners}, skipped (already exist): {skipped_cleaners}")
        print()


if __name__ == "__main__":
    seed()
