import pytest
from datetime import date, datetime, timezone, timedelta

from app.models import db, User, JobRequest, UserRole, JobStatus, ServiceType
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
    title="Test Job",
    description="Test description",
    service_type=ServiceType.partial,
    location="Test location",
    preferred_date=None,
    preferred_time_start=None,
    preferred_time_end=None,
    priority_window_end=None,
    deleted_at=None,
):
    job = JobRequest(
        end_user_id=end_user_id,
        cleaner_id=cleaner_id,
        title=title,
        description=description,
        service_type=service_type,
        location=location,
        preferred_date=preferred_date or date.today(),
        preferred_time_start=preferred_time_start,
        preferred_time_end=preferred_time_end,
        status=status,
        priority_window_end=priority_window_end,
        deleted_at=deleted_at,
    )
    db.session.add(job)
    db.session.commit()
    return job


def test_ban_user_success_end_user(app):
    with app.app_context():
        user = create_user("enduser@test.com", UserRole.end_user)

        result = AdminService.ban_user(user.id, reason="Malicious activity")

        updated = db.session.get(User, user.id)
        assert result["message"] == "User has been banned."
        assert result["user"]["id"] == user.id
        assert result["user"]["email"] == "enduser@test.com"
        assert result["user"]["role"] == "end_user"
        assert result["user"]["is_banned"] is True
        assert result["user"]["ban_reason"] == "Malicious activity"

        assert updated.is_banned is True
        assert updated.ban_reason == "Malicious activity"
        assert updated.banned_at is not None


def test_ban_user_not_found(app):
    with app.app_context():
        with pytest.raises(ValueError, match=r"not_found\|User not found\."):
            AdminService.ban_user(999999)


def test_ban_user_cannot_ban_administrator(app):
    with app.app_context():
        admin = create_user("admin@test.com", UserRole.administrator)

        with pytest.raises(ValueError, match=r"forbidden\|Cannot ban an administrator\."):
            AdminService.ban_user(admin.id)


def test_ban_user_already_banned(app):
    with app.app_context():
        user = create_user("banned@test.com", UserRole.end_user, is_banned=True)

        with pytest.raises(ValueError, match=r"already_banned\|User is already banned\."):
            AdminService.ban_user(user.id)


def test_ban_cleaner_unassigns_pending_and_confirmed_jobs(app):
    with app.app_context():
        cleaner = create_user("cleaner@test.com", UserRole.cleaner)
        end_user = create_user("client@test.com", UserRole.end_user)

        pending_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            priority_window_end=datetime.now(timezone.utc) + timedelta(hours=4),
            title="Pending job",
        )
        confirmed_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.confirmed,
            priority_window_end=datetime.now(timezone.utc) + timedelta(hours=4),
            title="Confirmed job",
        )

        result = AdminService.ban_user(cleaner.id, reason="Bad behavior")

        db.session.refresh(pending_job)
        db.session.refresh(confirmed_job)

        assert result["message"] == "User has been banned."

        assert pending_job.cleaner_id is None
        assert pending_job.priority_window_end is None
        assert pending_job.status == JobStatus.pending

        assert confirmed_job.cleaner_id is None
        assert confirmed_job.priority_window_end is None
        assert confirmed_job.status == JobStatus.pending


def test_ban_cleaner_cancels_in_progress_jobs(app):
    with app.app_context():
        cleaner = create_user("cleaner2@test.com", UserRole.cleaner)
        end_user = create_user("client2@test.com", UserRole.end_user)

        in_progress_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.in_progress,
            title="In progress job",
        )

        AdminService.ban_user(cleaner.id, reason="Abusive behavior")

        db.session.refresh(in_progress_job)
        assert in_progress_job.status == JobStatus.cancelled
        assert in_progress_job.cleaner_id == cleaner.id


def test_ban_end_user_cancels_active_jobs(app):
    with app.app_context():
        end_user = create_user("enduser2@test.com", UserRole.end_user)
        cleaner = create_user("cleaner3@test.com", UserRole.cleaner)

        pending_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Pending booking",
        )
        confirmed_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.confirmed,
            title="Confirmed booking",
        )
        in_progress_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.in_progress,
            title="In progress booking",
        )

        AdminService.ban_user(end_user.id, reason="Fraudulent bookings")

        db.session.refresh(pending_job)
        db.session.refresh(confirmed_job)
        db.session.refresh(in_progress_job)

        assert pending_job.status == JobStatus.cancelled
        assert confirmed_job.status == JobStatus.cancelled
        assert in_progress_job.status == JobStatus.cancelled


def test_ban_user_ignores_deleted_jobs(app):
    with app.app_context():
        end_user = create_user("enduser3@test.com", UserRole.end_user)
        cleaner = create_user("cleaner4@test.com", UserRole.cleaner)

        deleted_job = create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            deleted_at=datetime.now(timezone.utc),
            title="Deleted booking",
        )

        AdminService.ban_user(end_user.id, reason="Bad actor")

        db.session.refresh(deleted_job)
        assert deleted_job.status == JobStatus.pending