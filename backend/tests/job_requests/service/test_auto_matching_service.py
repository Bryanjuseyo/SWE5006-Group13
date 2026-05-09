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
        assert result["matches"][1]["cleaner_id"] == cleaner2.id
        assert result["matches"][0]["name"] == "Alice Tan"


def test_find_matching_cleaners_default_uses_continuous_pricing_score(app):
    with app.app_context():
        end_user = create_user("owner_continuous@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        gradual_cleaner = create_user("gradual_price@test.com", UserRole.cleaner)
        create_user_profile(gradual_cleaner.id, "Gradual", "Price")
        create_cleaner_profile(
            gradual_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("36.00"),
            years_experience=5,
        )

        band_edge_cleaner = create_user("band_edge@test.com", UserRole.cleaner)
        create_user_profile(band_edge_cleaner.id, "Band", "Edge")
        create_cleaner_profile(
            band_edge_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("35.00"),
            years_experience=4,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert result["matches"][0]["cleaner_id"] == gradual_cleaner.id
        assert result["matches"][1]["cleaner_id"] == band_edge_cleaner.id


def test_find_matching_cleaners_default_treats_zero_rate_as_free(app):
    with app.app_context():
        end_user = create_user("owner_free@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        free_cleaner = create_user("free_rate@test.com", UserRole.cleaner)
        create_user_profile(free_cleaner.id, "Free", "Rate")
        create_cleaner_profile(
            free_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("0.00"),
            years_experience=1,
        )

        paid_cleaner = create_user("paid_rate@test.com", UserRole.cleaner)
        create_user_profile(paid_cleaner.id, "Paid", "Rate")
        create_cleaner_profile(
            paid_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("30.00"),
            years_experience=1,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        assert result["matches"][0]["cleaner_id"] == free_cleaner.id
        assert result["matches"][1]["cleaner_id"] == paid_cleaner.id


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


def test_find_matching_cleaners_excludes_cleaners_with_different_service_type(app):
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


def test_find_matching_cleaners_excludes_cleaners_with_non_matching_availability(app):
    with app.app_context():
        end_user = create_user("owner_unavailable@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )

        unavailable_cleaner = create_user("unavailable@test.com", UserRole.cleaner)
        create_user_profile(unavailable_cleaner.id, "Unavailable", "Cleaner")
        unavailable_profile = create_cleaner_profile(
            unavailable_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=10,
        )
        create_availability(
            unavailable_profile.id,
            start_date=date(2026, 3, 27),
            end_date=date(2026, 3, 27),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        flexible_cleaner = create_user("flexible@test.com", UserRole.cleaner)
        create_user_profile(flexible_cleaner.id, "Flexible", "Cleaner")
        create_cleaner_profile(
            flexible_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("60.00"),
            years_experience=1,
        )

        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")

        cleaner_ids = [m["cleaner_id"] for m in result["matches"]]
        assert flexible_cleaner.id in cleaner_ids
        assert unavailable_cleaner.id not in cleaner_ids


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
        assert "Cleaner Best Cleaner has been assigned to the job." == result["message"]


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


def test_find_matching_cleaners_supports_lowest_price_strategy(app):
    with app.app_context():
        end_user = create_user("owner11@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cheaper_cleaner = create_user("cheap@test.com", UserRole.cleaner)
        create_user_profile(cheaper_cleaner.id, "Cheap", "Cleaner")
        create_cleaner_profile(
            cheaper_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=1,
        )

        experienced_cleaner = create_user("expensive@test.com", UserRole.cleaner)
        create_user_profile(experienced_cleaner.id, "Experienced", "Cleaner")
        create_cleaner_profile(
            experienced_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("60.00"),
            years_experience=10,
        )

        result = MatchingService.find_matching_cleaners(
            job.id,
            end_user.id,
            "end_user",
            strategy_name="lowest_price",
        )

        assert result["strategy"] == "lowest_price"
        assert result["matches"][0]["cleaner_id"] == cheaper_cleaner.id


def test_find_matching_cleaners_supports_highest_experience_strategy(app):
    with app.app_context():
        end_user = create_user("owner13@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        cheaper_cleaner = create_user("cheap_less_exp@test.com", UserRole.cleaner)
        create_user_profile(cheaper_cleaner.id, "Cheap", "LessExp")
        create_cleaner_profile(
            cheaper_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("20.00"),
            years_experience=1,
        )

        experienced_cleaner = create_user("experienced_high_rate@test.com", UserRole.cleaner)
        create_user_profile(experienced_cleaner.id, "Experienced", "HighRate")
        create_cleaner_profile(
            experienced_cleaner.id,
            service_type=ServiceType.partial,
            hourly_rate=Decimal("60.00"),
            years_experience=10,
        )

        result = MatchingService.find_matching_cleaners(
            job.id,
            end_user.id,
            "end_user",
            strategy_name="highest_experience",
        )

        assert result["strategy"] == "highest_experience"
        assert result["matches"][0]["cleaner_id"] == experienced_cleaner.id


def test_find_matching_cleaners_raises_invalid_strategy(app):
    with app.app_context():
        end_user = create_user("owner12@test.com", UserRole.end_user)
        job = create_job(
            end_user.id,
            service_type=ServiceType.partial,
            status=JobStatus.pending,
            preferred_date=date(2026, 3, 28),
        )

        with pytest.raises(
            ValueError,
            match=r"invalid_strategy\|strategy must be one of:",
        ):
            MatchingService.find_matching_cleaners(
                job.id,
                end_user.id,
                "end_user",
                strategy_name="unknown",
            )
