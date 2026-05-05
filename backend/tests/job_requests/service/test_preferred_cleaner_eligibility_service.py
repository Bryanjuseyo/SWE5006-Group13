"""
Preferred cleaner eligibility tests for create/edit job request flows.
"""
from datetime import date, time

import pytest

from app.models import (
    CleanerProfile,
    JobRequest,
    JobStatus,
    ServiceType,
    UserProfile,
    UserRole,
    db,
)
from app.services.cleaner_profile_service import CleanerProfileService
from app.services.job_request_service import JobRequestService


FUTURE_JOB_DATE = date(2099, 12, 31)
FUTURE_JOB_DATE_STR = FUTURE_JOB_DATE.isoformat()


def _add_profile(user, first_name="Test", last_name="Cleaner"):
    profile = UserProfile(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        city="Singapore",
    )
    db.session.add(profile)
    return profile


def _add_cleaner_profile(user, service_type=ServiceType.full):
    cleaner_profile = CleanerProfile(
        user_id=user.id,
        service_type=service_type,
        hourly_rate=30,
        years_experience=3,
    )
    db.session.add(cleaner_profile)
    return cleaner_profile


def _add_booking(
    owner_id,
    cleaner_id,
    *,
    status=JobStatus.confirmed,
    preferred_date=FUTURE_JOB_DATE,
    preferred_time_start=time(10, 0),
    preferred_time_end=time(12, 0),
    service_type=ServiceType.full,
):
    job = JobRequest(
        end_user_id=owner_id,
        cleaner_id=cleaner_id,
        title="Existing booking",
        service_type=service_type,
        location="123 Test Street",
        preferred_date=preferred_date,
        preferred_time_start=preferred_time_start,
        preferred_time_end=preferred_time_end,
        status=status,
    )
    db.session.add(job)
    return job


def _create_cleaner(make_user, email, service_type=ServiceType.full, first_name="Test"):
    cleaner = make_user(email=email, role=UserRole.cleaner)
    _add_profile(cleaner, first_name=first_name)
    _add_cleaner_profile(cleaner, service_type=service_type)
    return cleaner


def _job_request_payload(cleaner_id=None):
    payload = {
        "title": "House cleaning",
        "service_type": "full",
        "location": "123 Test Street",
        "preferred_date": FUTURE_JOB_DATE_STR,
        "preferred_time_start": "11:00",
        "preferred_time_end": "13:00",
    }
    if cleaner_id is not None:
        payload["cleaner_id"] = cleaner_id
    return payload


def test_list_cleaners_filters_service_and_bookings_without_requiring_slots(make_user):
    owner = make_user(email="owner-list@test.com", role=UserRole.end_user)
    eligible = _create_cleaner(make_user, "eligible@test.com", first_name="Eligible")
    booked = _create_cleaner(make_user, "booked@test.com", first_name="Booked")
    partial = _create_cleaner(
        make_user,
        "partial@test.com",
        service_type=ServiceType.partial,
        first_name="Partial",
    )
    _add_booking(owner.id, booked.id)
    db.session.commit()

    result = CleanerProfileService.list_cleaners(
        service_type="full",
        preferred_date=FUTURE_JOB_DATE_STR,
        preferred_time_start="11:00",
        preferred_time_end="13:00",
    )

    cleaner_ids = {cleaner["user_id"] for cleaner in result["cleaners"]}
    assert eligible.id in cleaner_ids
    assert booked.id not in cleaner_ids
    assert partial.id not in cleaner_ids


def test_create_job_request_allows_preferred_cleaner_without_availability_slots(make_user):
    owner = make_user(email="owner-create@test.com", role=UserRole.end_user)
    cleaner = _create_cleaner(make_user, "open-cleaner@test.com")
    db.session.commit()

    result = JobRequestService.create_job_request(
        end_user_id=owner.id,
        data=_job_request_payload(cleaner.id),
    )

    assert result["job_request"]["cleaner_id"] == cleaner.id


def test_create_job_request_rejects_booked_preferred_cleaner(make_user):
    owner = make_user(email="owner-booked@test.com", role=UserRole.end_user)
    cleaner = _create_cleaner(make_user, "busy-cleaner@test.com")
    _add_booking(owner.id, cleaner.id)
    db.session.commit()

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=owner.id,
            data=_job_request_payload(cleaner.id),
        )

    assert "already has a booking" in str(e.value)


def test_create_job_request_rejects_preferred_cleaner_with_different_service_type(make_user):
    owner = make_user(email="owner-service@test.com", role=UserRole.end_user)
    cleaner = _create_cleaner(
        make_user,
        "partial-cleaner@test.com",
        service_type=ServiceType.partial,
    )
    db.session.commit()

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=owner.id,
            data=_job_request_payload(cleaner.id),
        )

    assert "does not offer the requested service type" in str(e.value)


def test_update_job_request_rejects_booked_preferred_cleaner(make_user):
    owner = make_user(email="owner-edit@test.com", role=UserRole.end_user)
    cleaner = _create_cleaner(make_user, "busy-edit-cleaner@test.com")
    job_to_edit = _add_booking(
        owner.id,
        None,
        status=JobStatus.pending,
        preferred_time_start=time(11, 0),
        preferred_time_end=time(13, 0),
    )
    _add_booking(owner.id, cleaner.id)
    db.session.commit()

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=job_to_edit.id,
            user_id=owner.id,
            role="end_user",
            data={"cleaner_id": cleaner.id},
        )

    assert "already has a booking" in str(e.value)


def test_update_job_request_excludes_current_confirmed_job_from_booking_conflict(make_user):
    owner = make_user(email="owner-self-conflict@test.com", role=UserRole.end_user)
    cleaner = _create_cleaner(make_user, "assigned-cleaner@test.com")
    job = _add_booking(owner.id, cleaner.id, status=JobStatus.confirmed)
    db.session.commit()

    result = JobRequestService.update_job_request(
        job_request_id=job.id,
        user_id=owner.id,
        role="end_user",
        data={"preferred_time_end": "13:00"},
    )

    assert result["job_request"]["id"] == job.id
    assert result["job_request"]["preferred_time_end"] == "13:00:00"
