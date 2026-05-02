import os
import sys
from datetime import date, time
from decimal import Decimal

# Allows this script to import from backend/app when run from backend/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import (
    db,
    User,
    UserProfile,
    CleanerProfile,
    CleaningService,
    CleanerOfferedService,
    CleanerAvailability,
    UserRole,
    ServiceType,
)


DEFAULT_PASSWORD = "Password1"


SINGAPORE_ADDRESSES = [
    "10 Tampines Central 1, Singapore 529536",
    "21 Jurong East Street 31, Singapore 609517",
    "55 Tiong Bahru Road, Singapore 160055",
    "88 Bedok North Street 4, Singapore 460088",
    "12 Ang Mo Kio Avenue 3, Singapore 560012",
    "7 Bishan Street 13, Singapore 570007",
    "31 Clementi Avenue 2, Singapore 120031",
    "19 Serangoon North Avenue 1, Singapore 550019",
    "46 Yishun Ring Road, Singapore 760046",
    "23 Bukit Batok Street 52, Singapore 650023",
    "5 Hougang Avenue 8, Singapore 530005",
    "77 Pasir Ris Drive 6, Singapore 510077",
    "34 Toa Payoh Lorong 5, Singapore 310034",
    "9 Punggol Field Walk, Singapore 828749",
    "60 Sengkang East Way, Singapore 540060",
    "18 Woodlands Drive 16, Singapore 730018",
    "42 Choa Chu Kang Avenue 4, Singapore 680042",
    "3 Queenstown Road, Singapore 149053",
    "25 Marine Parade Road, Singapore 449536",
    "11 Bukit Timah Road, Singapore 229847",
    "70 Geylang Bahru, Singapore 330070",
    "16 Kallang Place, Singapore 339156",
    "29 Lavender Street, Singapore 338729",
    "6 Holland Avenue, Singapore 271006",
    "52 Commonwealth Drive, Singapore 140052",
]


def make_phone_number(index):
    """
    Generates Singapore-style mobile numbers.
    Example:
    90000001
    90000002
    ...
    """
    return f"9{index:07d}"


def get_address(index):
    return SINGAPORE_ADDRESSES[(index - 1) % len(SINGAPORE_ADDRESSES)]


def get_or_create_user(email, password, role):
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print(f"User already exists: {email}")
        return existing_user

    user = User(
        email=email,
        role=role,
        two_factor_enabled=False,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    print(f"Created user: {email}")
    return user


def get_or_create_user_profile(user, first_name, last_name, phone, address, city="Singapore"):
    existing_profile = UserProfile.query.filter_by(user_id=user.id).first()

    if existing_profile:
        print(f"UserProfile already exists for: {user.email}")
        return existing_profile

    profile = UserProfile(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
        city=city,
    )

    db.session.add(profile)
    db.session.flush()

    print(f"Created UserProfile for: {user.email}")
    return profile


def get_or_create_cleaning_service(name, description):
    existing_service = CleaningService.query.filter_by(name=name).first()

    if existing_service:
        print(f"CleaningService already exists: {name}")
        return existing_service

    service = CleaningService(
        name=name,
        description=description,
    )

    db.session.add(service)
    db.session.flush()

    print(f"Created CleaningService: {name}")
    return service


def get_or_create_cleaner_profile(user, index):
    existing_cleaner_profile = CleanerProfile.query.filter_by(user_id=user.id).first()

    if existing_cleaner_profile:
        print(f"CleanerProfile already exists for: {user.email}")
        return existing_cleaner_profile

    service_type = ServiceType.full if index % 2 == 0 else ServiceType.partial

    cleaner_profile = CleanerProfile(
        user_id=user.id,
        service_type=service_type,
        hourly_rate=Decimal(str(20 + index)),
        years_experience=(index % 10) + 1,
    )

    db.session.add(cleaner_profile)
    db.session.flush()

    print(f"Created CleanerProfile for: {user.email}")
    return cleaner_profile


def get_or_create_cleaner_offered_service(cleaner_profile, cleaning_service, custom_price):
    existing_offered_service = CleanerOfferedService.query.filter_by(
        cleaner_profile_id=cleaner_profile.id,
        cleaning_service_id=cleaning_service.id,
    ).first()

    if existing_offered_service:
        print(f"CleanerOfferedService already exists: {cleaning_service.name}")
        return existing_offered_service

    offered_service = CleanerOfferedService(
        cleaner_profile_id=cleaner_profile.id,
        cleaning_service_id=cleaning_service.id,
        custom_price=Decimal(str(custom_price)),
    )

    db.session.add(offered_service)
    db.session.flush()

    print(f"Created CleanerOfferedService: {cleaning_service.name}")
    return offered_service


def get_or_create_cleaner_availability(cleaner_profile, index):
    existing_availability = CleanerAvailability.query.filter_by(
        cleaner_profile_id=cleaner_profile.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    ).first()

    if existing_availability:
        print(f"CleanerAvailability already exists for cleaner_profile_id={cleaner_profile.id}")
        return existing_availability

    availability = CleanerAvailability(
        cleaner_profile_id=cleaner_profile.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        start_time=time(9, 0),
        end_time=time(18, 0),
    )

    db.session.add(availability)
    db.session.flush()

    print(f"Created CleanerAvailability for cleaner_profile_id={cleaner_profile.id}")
    return availability


def seed_admin():
    admin = get_or_create_user(
        email="admin@example.com",
        password=DEFAULT_PASSWORD,
        role=UserRole.administrator,
    )

    get_or_create_user_profile(
        user=admin,
        first_name="Admin",
        last_name="1",
        phone="90000000",
        address="1 Raffles Place, Singapore 048616",
    )


def seed_cleaning_services():
    regular_cleaning = get_or_create_cleaning_service(
        name="Regular Cleaning",
        description="General home cleaning service.",
    )

    deep_cleaning = get_or_create_cleaning_service(
        name="Deep Cleaning",
        description="Detailed full-house cleaning service.",
    )

    move_in_out_cleaning = get_or_create_cleaning_service(
        name="Move In/Out Cleaning",
        description="Cleaning service for moving in or moving out.",
    )

    office_cleaning = get_or_create_cleaning_service(
        name="Office Cleaning",
        description="Cleaning service for office spaces.",
    )

    return [
        regular_cleaning,
        deep_cleaning,
        move_in_out_cleaning,
        office_cleaning,
    ]


def seed_cleaners(cleaning_services):
    for index in range(1, 26):
        email = f"cleaner{index}@example.com"

        cleaner = get_or_create_user(
            email=email,
            password=DEFAULT_PASSWORD,
            role=UserRole.cleaner,
        )

        get_or_create_user_profile(
            user=cleaner,
            first_name="Cleaner",
            last_name=str(index),
            phone=make_phone_number(index),
            address=get_address(index),
        )

        cleaner_profile = get_or_create_cleaner_profile(
            user=cleaner,
            index=index,
        )

        # Give every cleaner at least 2 offered services.
        get_or_create_cleaner_offered_service(
            cleaner_profile=cleaner_profile,
            cleaning_service=cleaning_services[index % len(cleaning_services)],
            custom_price=20 + index,
        )

        get_or_create_cleaner_offered_service(
            cleaner_profile=cleaner_profile,
            cleaning_service=cleaning_services[(index + 1) % len(cleaning_services)],
            custom_price=25 + index,
        )

        get_or_create_cleaner_availability(
            cleaner_profile=cleaner_profile,
            index=index,
        )


def seed_users():
    for index in range(1, 26):
        email = f"user{index}@example.com"

        user = get_or_create_user(
            email=email,
            password=DEFAULT_PASSWORD,
            role=UserRole.end_user,
        )

        get_or_create_user_profile(
            user=user,
            first_name="User",
            last_name=str(index),
            phone=make_phone_number(index + 100),
            address=get_address(index),
        )


def main():
    app = create_app()

    with app.app_context():
        try:
            print("Starting database seed...")

            seed_admin()

            cleaning_services = seed_cleaning_services()

            seed_cleaners(cleaning_services)

            seed_users()

            db.session.commit()

            print("Database seed completed successfully.")

        except Exception as error:
            db.session.rollback()
            print(f"Database seed failed: {error}")
            raise


if __name__ == "__main__":
    main()