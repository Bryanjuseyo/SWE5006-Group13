from datetime import date, datetime, timezone, timedelta

import pytest

from app.models import db, User, JobRequest, UserRole, ServiceType, JobStatus
from app.services.admin_service import AdminService


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


def create_job(
    *,
    end_user_id,
    cleaner_id=None,
    status=JobStatus.pending,
    service_type=ServiceType.partial,
    preferred_date=None,
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
        preferred_time_start=None,
        preferred_time_end=None,
        status=status,
        deleted_at=deleted_at,
    )
    db.session.add(job)
    db.session.commit()
    return job


def test_get_all_bookings_returns_all_non_deleted_bookings(app):
    with app.app_context():
        end_user = create_user("end@test.com", UserRole.end_user)
        cleaner = create_user("cleaner@test.com", UserRole.cleaner)

        job1 = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Kitchen Cleaning",
        )
        job2 = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.completed,
            title="Bathroom Cleaning",
        )
        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.cancelled,
            title="Deleted Job",
            deleted_at=datetime.now(timezone.utc),
        )

        result = AdminService.get_all_bookings()

        titles = [job["title"] for job in result["job_requests"]]
        assert len(result["job_requests"]) == 2
        assert job1.title in titles
        assert job2.title in titles
        assert "Deleted Job" not in titles


def test_get_all_bookings_filters_by_status(app):
    with app.app_context():
        end_user = create_user("end2@test.com", UserRole.end_user)
        cleaner = create_user("cleaner2@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Pending Job",
        )
        confirmed_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.confirmed,
            title="Confirmed Job",
        )

        result = AdminService.get_all_bookings(status_filter="confirmed")

        assert len(result["job_requests"]) == 1
        assert result["job_requests"][0]["id"] == confirmed_job.id
        assert result["job_requests"][0]["status"] == "confirmed"


def test_get_all_bookings_filters_by_search(app):
    with app.app_context():
        end_user = create_user("end3@test.com", UserRole.end_user)
        cleaner = create_user("cleaner3@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Kitchen Deep Clean",
        )
        bathroom_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Bathroom Scrub",
        )

        result = AdminService.get_all_bookings(search="bathroom")

        assert len(result["job_requests"]) == 1
        assert result["job_requests"][0]["id"] == bathroom_job.id
        assert result["job_requests"][0]["title"] == "Bathroom Scrub"


def test_get_all_bookings_filters_by_status_and_search(app):
    with app.app_context():
        end_user = create_user("end4@test.com", UserRole.end_user)
        cleaner = create_user("cleaner4@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Kitchen Cleaning",
        )
        matched_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.confirmed,
            title="Kitchen Deep Cleaning",
        )
        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.confirmed,
            title="Bathroom Cleaning",
        )

        result = AdminService.get_all_bookings(
            status_filter="confirmed",
            search="kitchen",
        )

        assert len(result["job_requests"]) == 1
        assert result["job_requests"][0]["id"] == matched_job.id


def test_get_all_bookings_invalid_status_raises_error(app):
    with app.app_context():
        with pytest.raises(ValueError, match=r"invalid_status\|status must be one of:"):
            AdminService.get_all_bookings(status_filter="bad_status")


def test_get_all_bookings_returns_empty_when_no_match(app):
    with app.app_context():
        end_user = create_user("end5@test.com", UserRole.end_user)
        cleaner = create_user("cleaner5@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Living Room Cleaning",
        )

        result = AdminService.get_all_bookings(search="balcony")

        assert result["job_requests"] == []


def test_get_all_bookings_orders_by_created_at_desc(app):
    with app.app_context():
        end_user = create_user("end6@test.com", UserRole.end_user)
        cleaner = create_user("cleaner6@test.com", UserRole.cleaner)

        older_job = JobRequest(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            title="Older Job",
            description="Test description",
            service_type=ServiceType.partial,
            location="Test location",
            preferred_date=date.today(),
            status=JobStatus.pending,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        newer_job = JobRequest(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            title="Newer Job",
            description="Test description",
            service_type=ServiceType.partial,
            location="Test location",
            preferred_date=date.today(),
            status=JobStatus.pending,
            created_at=datetime.now(timezone.utc),
        )

        db.session.add_all([older_job, newer_job])
        db.session.commit()

        result = AdminService.get_all_bookings()

        assert result["job_requests"][0]["title"] == "Newer Job"
        assert result["job_requests"][1]["title"] == "Older Job"
