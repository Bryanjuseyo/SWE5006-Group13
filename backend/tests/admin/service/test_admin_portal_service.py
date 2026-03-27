from datetime import date, datetime, timezone

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


def test_get_dashboard_stats_returns_correct_counts(app):
    with app.app_context():
        end_user_1 = create_user("end1@test.com", UserRole.end_user)
        end_user_2 = create_user("end2@test.com", UserRole.end_user, is_banned=True)
        cleaner_1 = create_user("cleaner1@test.com", UserRole.cleaner)
        cleaner_2 = create_user("cleaner2@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user_1.id,
            cleaner_id=cleaner_1.id,
            status=JobStatus.pending,
            title="Pending Job",
        )
        create_job(
            end_user_id=end_user_1.id,
            cleaner_id=cleaner_1.id,
            status=JobStatus.confirmed,
            title="Confirmed Job",
        )
        create_job(
            end_user_id=end_user_1.id,
            cleaner_id=cleaner_1.id,
            status=JobStatus.in_progress,
            title="In Progress Job",
        )
        create_job(
            end_user_id=end_user_2.id,
            cleaner_id=cleaner_2.id,
            status=JobStatus.completed,
            title="Completed Job",
        )
        create_job(
            end_user_id=end_user_2.id,
            cleaner_id=cleaner_2.id,
            status=JobStatus.cancelled,
            title="Cancelled Job",
        )
        create_job(
            end_user_id=end_user_2.id,
            cleaner_id=cleaner_2.id,
            status=JobStatus.rejected,
            title="Rejected Job",
        )

        result = AdminService.get_dashboard_stats()

        assert result["users"]["total"] == 5
        assert result["users"]["end_users"] == 2
        assert result["users"]["cleaners"] == 2
        assert result["users"]["administrators"] == 1
        assert result["users"]["banned"] == 1

        assert result["jobs"]["total"] == 6
        assert result["jobs"]["pending"] == 1
        assert result["jobs"]["confirmed"] == 1
        assert result["jobs"]["in_progress"] == 1
        assert result["jobs"]["completed"] == 1
        assert result["jobs"]["cancelled"] == 1
        assert result["jobs"]["rejected"] == 1


def test_get_dashboard_stats_ignores_deleted_jobs(app):
    with app.app_context():
        end_user = create_user("end@test.com", UserRole.end_user)
        cleaner = create_user("cleaner@test.com", UserRole.cleaner)

        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.pending,
            title="Active Job",
            deleted_at=None,
        )
        create_job(
            end_user_id=end_user.id,
            cleaner_id=cleaner.id,
            status=JobStatus.completed,
            title="Deleted Job",
            deleted_at=datetime.now(timezone.utc),
        )

        result = AdminService.get_dashboard_stats()

        assert result["jobs"]["total"] == 1
        assert result["jobs"]["pending"] == 1
        assert result["jobs"]["completed"] == 0
        assert result["jobs"]["confirmed"] == 0
        assert result["jobs"]["in_progress"] == 0
        assert result["jobs"]["cancelled"] == 0
        assert result["jobs"]["rejected"] == 0


def test_get_dashboard_stats_returns_zero_when_no_data(app):
    with app.app_context():
        result = AdminService.get_dashboard_stats()

        assert result["users"]["total"] == 0
        assert result["users"]["end_users"] == 0
        assert result["users"]["cleaners"] == 0
        assert result["users"]["administrators"] == 0
        assert result["users"]["banned"] == 0

        assert result["jobs"]["total"] == 0
        assert result["jobs"]["pending"] == 0
        assert result["jobs"]["confirmed"] == 0
        assert result["jobs"]["in_progress"] == 0
        assert result["jobs"]["completed"] == 0
        assert result["jobs"]["cancelled"] == 0
        assert result["jobs"]["rejected"] == 0
