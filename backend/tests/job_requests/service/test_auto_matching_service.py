from datetime import date, time, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from app.models import (
    db,
    PRIORITY_WINDOW_HOURS,
    User,
    UserProfile,
    CleanerProfile,
    CleanerAvailability,
    JobRequest,
    UserRole,
    ServiceType,
    JobStatus,
)
from app.services.matching_service import MatchingService


def create_user(email, role=UserRole.end_user, is_banned=False):
    user = User(
        email=email,
        password_hash="hashed_password",
        role=role,
        is_banned=is_banned,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_user_profile(user_id, first_name="Test", last_name="User"):
    profile = UserProfile(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        phone="91234567",
        address="123 Test Street",
        city="Singapore",
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def create_cleaner_profile(
    user_id,
    service_type=ServiceType.partial,
    hourly_rate=Decimal("20.00"),
    years_experience=0,
):
    profile = CleanerProfile(
        user_id=user_id,
        service_type=service_type,
        hourly_rate=hourly_rate,
        years_experience=years_experience,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def create_availability(
    cleaner_profile_id,
    start_date,
    end_date,
    start_time=None,
    end_time=None,
):
    slot = CleanerAvailability(
        cleaner_profile_id=cleaner_profile_id,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(slot)
    db.session.commit()
    return slot


def create_job(
    end_user_id,
    service_type=ServiceType.partial,
    status=JobStatus.pending,
    preferred_date=None,
    preferred_time_start=None,
    preferred_time_end=None,
    cleaner_id=None,
    deleted_at=None,
    title="Test Job",
):
    job = JobRequest(
        end_user_id=end_user_id,
        cleaner_id=cleaner_id,
        title=title,
        description="Test description",
        service_type=service_type,
        location="Test location",
        preferred_date=preferred_date or date.today(),
        preferred_time_start=preferred_time_start,
        preferred_time_end=preferred_time_end,
        status=status,
        deleted_at=deleted_at,
    )
    db.session.add(job)
    db.session.commit()
    return job


def test_score_cleaner_returns_zero_when_service_type_mismatch(app):
    with app.app_context():
        cleaner = create_user("cleaner1@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.full,
            hourly_rate=Decimal("20.00"),
            years_experience=5,
        )
        end_user = create_user("client1@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        assert score == 0.0


def test_score_cleaner_gives_full_availability_score_for_time_overlap(app):
    with app.app_context():
        cleaner = create_user("cleaner2@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=5,
        )
        create_availability(
            profile.id,
            start_date=date(2026, 3, 28),
            end_date=date(2026, 3, 28),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        end_user = create_user("client2@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        # 40 service match + 30 availability + 10 exp(5*2 capped) + 10 low rate
        assert score == 90.0


def test_score_cleaner_gives_availability_score_for_all_day_slot(app):
    with app.app_context():
        cleaner = create_user("cleaner3@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("35.00"),
            years_experience=3,
        )
        create_availability(
            profile.id,
            start_date=date(2026, 3, 28),
            end_date=date(2026, 3, 28),
            start_time=None,
            end_time=None,
        )

        end_user = create_user("client3@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
            preferred_time_start=time(14, 0),
            preferred_time_end=time(16, 0),
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        # 40 + 30 + 6 + 7
        assert score == 83.0


def test_score_cleaner_gives_availability_score_when_job_has_no_start_time(app):
    with app.app_context():
        cleaner = create_user("cleaner4@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("50.00"),
            years_experience=2,
        )
        create_availability(
            profile.id,
            start_date=date(2026, 3, 28),
            end_date=date(2026, 3, 29),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        end_user = create_user("client4@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
            preferred_time_start=None,
            preferred_time_end=None,
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        # 40 + 30 + 4 + 4
        assert score == 78.0


def test_score_cleaner_gives_partial_credit_when_no_availability_set(app):
    with app.app_context():
        cleaner = create_user("cleaner5@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("60.00"),
            years_experience=1,
        )

        end_user = create_user("client5@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        # 40 + 15 + 2 + 1
        assert score == 58.0


def test_score_cleaner_caps_experience_bonus_at_20(app):
    with app.app_context():
        cleaner = create_user("cleaner6@test.com", UserRole.cleaner)
        profile = create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=50,
        )

        end_user = create_user("client6@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            preferred_date=date(2026, 3, 28),
        )

        score = MatchingService._score_cleaner(job, cleaner, profile)

        # 40 + 15 + 20 cap + 10
        assert score == 85.0


def test_find_matching_cleaners_success_sorted_descending(app):
    with app.app_context():
        end_user = create_user("owner@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )

        cleaner1 = create_user("cleanerA@test.com", UserRole.cleaner)
        create_user_profile(cleaner1.id, "Alice", "Tan")
        profile1 = create_cleaner_profile(
            cleaner1.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=5,
        )
        create_availability(
            profile1.id,
            start_date=date(2026, 3, 28),
            end_date=date(2026, 3, 28),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        cleaner2 = create_user("cleanerB@test.com", UserRole.cleaner)
        create_user_profile(cleaner2.id, "Bob", "Lee")
        profile2 = create_cleaner_profile(
            cleaner2.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("50.00"),
            years_experience=1,
        )
        create_availability(
            profile2.id,
            start_date=date(2026, 3, 28),
            end_date=date(2026, 3, 28),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert result["job_request_id"] == job.id
        assert len(result["matches"]) == 2
        assert result["matches"][0]["cleaner_id"] == cleaner1.id
        assert result["matches"][0]["name"] == "Alice Tan"
        assert result["matches"][0]["score"] > result["matches"][1]["score"]


def test_find_matching_cleaners_returns_top_5_only(app):
    with app.app_context():
        end_user = create_user("owner2@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        for i in range(6):
            cleaner = create_user(f"cleaner{i}@test.com", UserRole.cleaner)
            create_user_profile(cleaner.id, f"Cleaner{i}", "User")
            create_cleaner_profile(
                cleaner.id,
                service_type=ServiceType.partial,
                hourly_rate=Decimal("20.00"),
                years_experience=i,
            )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert len(result["matches"]) == 5


def test_find_matching_cleaners_excludes_banned_cleaners(app):
    with app.app_context():
        end_user = create_user("owner3@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        active_cleaner = create_user("active@test.com", UserRole.cleaner, is_banned=False)
        create_user_profile(active_cleaner.id, "Active", "Cleaner")
        create_cleaner_profile(
            active_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=5,
        )

        banned_cleaner = create_user("banned@test.com", UserRole.cleaner, is_banned=True)
        create_user_profile(banned_cleaner.id, "Banned", "Cleaner")
        create_cleaner_profile(
            banned_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=10,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        cleaner_ids = [m["cleaner_id"] for m in result["matches"]]
        assert active_cleaner.id in cleaner_ids
        assert banned_cleaner.id not in cleaner_ids


def test_find_matching_cleaners_excludes_zero_score_cleaners(app):
    with app.app_context():
        end_user = create_user("owner4@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        wrong_type_cleaner = create_user("wrongtype@test.com", UserRole.cleaner)
        create_user_profile(wrong_type_cleaner.id, "Wrong", "Type")
        create_cleaner_profile(
            wrong_type_cleaner.id,
            service_type=ServiceType.full,
            hourly_rate=Decimal("20.00"),
            years_experience=10,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert result["matches"] == []


def test_find_matching_cleaners_falls_back_to_email_when_no_user_profile(app):
    with app.app_context():
        end_user = create_user("owner5@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cleaner = create_user("noprof@test.com", UserRole.cleaner)
        create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=3,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert len(result["matches"]) == 1
        assert result["matches"][0]["name"] == "noprof@test.com"


def test_find_matching_cleaners_raises_not_found(app):
    with app.app_context():
        with pytest.raises(ValueError, match=r"not_found\|Job request not found\."):
            MatchingService.find_matching_cleaners(999999, 1, "end_user")


def test_find_matching_cleaners_raises_forbidden_for_non_owner_end_user(app):
    with app.app_context():
        owner = create_user("realowner@test.com", UserRole.end_user)
        other_user = create_user("other@test.com", UserRole.end_user)

        job = create_job(
            owner.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        with pytest.raises(
            ValueError,
            match=r"forbidden\|You are not authorized to match cleaners for this job\.",
        ):
            MatchingService.find_matching_cleaners(job.id, other_user.id, "end_user")


def test_find_matching_cleaners_raises_invalid_status(app):
    with app.app_context():
        end_user = create_user("owner6@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.confirmed,
            preferred_date=date(2026, 3, 28),
        )

        with pytest.raises(
            ValueError,
            match=r"invalid_status\|Can only match cleaners for pending jobs\.",
        ):
            MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")


def test_find_matching_cleaners_ignores_deleted_jobs(app):
    with app.app_context():
        end_user = create_user("owner7@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
            deleted_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError, match=r"not_found\|Job request not found\."):
            MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")


def test_auto_assign_cleaner_success(app):
    with app.app_context():
        end_user = create_user("owner8@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cleaner = create_user("bestcleaner@test.com", UserRole.cleaner)
        create_user_profile(cleaner.id, "Best", "Cleaner")
        create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=8,
        )

        result = MatchingService.auto_assign_cleaner(job.id, end_user.id, "end_user")

        updated_job = db.session.get(JobRequest, job.id)

        assert result["assigned_cleaner"]["cleaner_id"] == cleaner.id
        assert result["assigned_cleaner"]["name"] == "Best Cleaner"
        assert result["job_request"]["id"] == job.id
        assert updated_job.cleaner_id == cleaner.id
        assert updated_job.priority_window_end is not None
        assert f"Cleaner Best Cleaner has been assigned to the job." == result["message"]


def test_auto_assign_cleaner_sets_priority_window_end(app):
    with app.app_context():
        end_user = create_user("owner9@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cleaner = create_user("priority@test.com", UserRole.cleaner)
        create_user_profile(cleaner.id, "Priority", "Cleaner")
        create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=4,
        )

        before = datetime.now(timezone.utc)
        MatchingService.auto_assign_cleaner(job.id, end_user.id, "end_user")
        after = datetime.now(timezone.utc)

        updated_job = db.session.get(JobRequest, job.id)

        lower_bound = before + timedelta(hours=PRIORITY_WINDOW_HOURS)
        upper_bound = after + timedelta(hours=PRIORITY_WINDOW_HOURS)

        assert updated_job.priority_window_end is not None
        assert lower_bound <= updated_job.priority_window_end <= upper_bound


def test_auto_assign_cleaner_raises_no_match(app):
    with app.app_context():
        end_user = create_user("owner10@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cleaner = create_user("nomatch@test.com", UserRole.cleaner)
        create_user_profile(cleaner.id, "No", "Match")
        create_cleaner_profile(
            cleaner.id,
            service_type=ServiceType.full,
            hourly_rate=Decimal("20.00"),
            years_experience=5,
        )

        with pytest.raises(
            ValueError,
            match=r"no_match\|No suitable cleaners found for this job\.",
        ):
            MatchingService.auto_assign_cleaner(job.id, end_user.id, "end_user")
