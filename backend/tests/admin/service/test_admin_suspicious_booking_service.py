from datetime import date, datetime, timezone

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
    title="Suspicious Job",
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


def test_reject_booking_success(app):
    with app.app_context():
        end_user = create_user("end@test.com", UserRole.end_user)
        cleaner = create_user("cleaner@test.com", UserRole.cleaner)

        job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Suspicious Booking",
        )

        result = AdminService.reject_booking(job.id, reason="Suspicious activity")

        updated_job = db.session.get(JobRequest, job.id)

        assert result["message"] == "Booking has been rejected."
        assert result["job_request"]["id"] == job.id
        assert result["job_request"]["status"] == "rejected"
        assert updated_job.status == JobStatus.rejected


def test_reject_booking_not_found(app):
    with app.app_context():
        with pytest.raises(ValueError, match=r"not_found\|Job request not found\."):
            AdminService.reject_booking(999999, reason="Suspicious activity")


def test_reject_booking_rejects_completed_booking_as_invalid(app):
    with app.app_context():
        end_user = create_user("end2@test.com", UserRole.end_user)
        cleaner = create_user("cleaner2@test.com", UserRole.cleaner)

        job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.completed,
            title="Completed Booking",
        )

        with pytest.raises(
            ValueError,
            match=r"invalid_status\|Cannot reject a completed or already rejected booking\.",
        ):
            AdminService.reject_booking(job.id, reason="Too late")

        unchanged_job = db.session.get(JobRequest, job.id)
        assert unchanged_job.status == JobStatus.completed


def test_reject_booking_rejects_already_rejected_booking_as_invalid(app):
    with app.app_context():
        end_user = create_user("end3@test.com", UserRole.end_user)
        cleaner = create_user("cleaner3@test.com", UserRole.cleaner)

        job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.rejected,
            title="Already Rejected Booking",
        )

        with pytest.raises(
            ValueError,
            match=r"invalid_status\|Cannot reject a completed or already rejected booking\.",
        ):
            AdminService.reject_booking(job.id, reason="Duplicate reject")

        unchanged_job = db.session.get(JobRequest, job.id)
        assert unchanged_job.status == JobStatus.rejected


def test_reject_booking_ignores_deleted_jobs(app):
    with app.app_context():
        end_user = create_user("end4@test.com", UserRole.end_user)
        cleaner = create_user("cleaner4@test.com", UserRole.cleaner)

        job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            deleted_at=datetime.now(timezone.utc),
            title="Deleted Suspicious Booking",
        )

        with pytest.raises(ValueError, match=r"not_found\|Job request not found\."):
            AdminService.reject_booking(job.id, reason="Suspicious activity")
