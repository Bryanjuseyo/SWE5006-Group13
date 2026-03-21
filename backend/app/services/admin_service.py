from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.models import (
    db, User, UserRole, UserProfile, JobRequest, JobStatus, CleanerProfile,
)


class AdminService:

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        total_users = User.query.count()
        total_end_users = User.query.filter_by(role=UserRole.end_user).count()
        total_cleaners = User.query.filter_by(role=UserRole.cleaner).count()
        total_admins = User.query.filter_by(role=UserRole.administrator).count()
        banned_users = User.query.filter_by(is_banned=True).count()

        total_jobs = JobRequest.query.filter(JobRequest.deleted_at.is_(None)).count()
        pending_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.pending,
        ).count()
        confirmed_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.confirmed,
        ).count()
        in_progress_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.in_progress,
        ).count()
        completed_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.completed,
        ).count()
        cancelled_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.cancelled,
        ).count()
        rejected_jobs = JobRequest.query.filter(
            JobRequest.deleted_at.is_(None),
            JobRequest.status == JobStatus.rejected,
        ).count()

        return {
            "users": {
                "total": total_users,
                "end_users": total_end_users,
                "cleaners": total_cleaners,
                "administrators": total_admins,
                "banned": banned_users,
            },
            "jobs": {
                "total": total_jobs,
                "pending": pending_jobs,
                "confirmed": confirmed_jobs,
                "in_progress": in_progress_jobs,
                "completed": completed_jobs,
                "cancelled": cancelled_jobs,
                "rejected": rejected_jobs,
            },
        }

    @staticmethod
    def get_all_users(
        role_filter: Optional[str] = None,
        banned_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = User.query

        if role_filter:
            try:
                role_enum = UserRole(role_filter)
                query = query.filter_by(role=role_enum)
            except ValueError:
                valid = ", ".join([r.value for r in UserRole])
                raise ValueError(f"invalid_role|role must be one of: {valid}.")

        if banned_filter is not None:
            if banned_filter == "true":
                query = query.filter_by(is_banned=True)
            elif banned_filter == "false":
                query = query.filter_by(is_banned=False)

        if search:
            search_term = f"%{search}%"
            query = query.filter(User.email.ilike(search_term))

        query = query.order_by(User.created_at.desc())
        users = query.all()

        result = []
        for u in users:
            user_dict = u.to_dict()
            profile = UserProfile.query.filter_by(user_id=u.id).first()
            if profile:
                user_dict["profile"] = profile.to_dict()
            else:
                user_dict["profile"] = None
            result.append(user_dict)

        return {"users": result}

    @staticmethod
    def ban_user(user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("not_found|User not found.")

        if user.role == UserRole.administrator:
            raise ValueError("forbidden|Cannot ban an administrator.")

        if user.is_banned:
            raise ValueError("already_banned|User is already banned.")

        user.is_banned = True
        user.banned_at = datetime.now(timezone.utc)
        user.ban_reason = reason

        # Handle active job requests for the banned user
        if user.role == UserRole.cleaner:
            # Unassign from pending/confirmed jobs - open them to other cleaners
            assigned_jobs = JobRequest.query.filter(
                JobRequest.cleaner_id == user_id,
                JobRequest.status.in_([JobStatus.pending, JobStatus.confirmed]),
                JobRequest.deleted_at.is_(None),
            ).all()
            for job in assigned_jobs:
                job.cleaner_id = None
                job.priority_window_end = None
                job.status = JobStatus.pending

            # Cancel in-progress jobs
            in_progress_jobs = JobRequest.query.filter(
                JobRequest.cleaner_id == user_id,
                JobRequest.status == JobStatus.in_progress,
                JobRequest.deleted_at.is_(None),
            ).all()
            for job in in_progress_jobs:
                job.status = JobStatus.cancelled

        elif user.role == UserRole.end_user:
            # Cancel all active jobs created by the banned end user
            active_jobs = JobRequest.query.filter(
                JobRequest.end_user_id == user_id,
                JobRequest.status.in_([
                    JobStatus.pending, JobStatus.confirmed, JobStatus.in_progress,
                ]),
                JobRequest.deleted_at.is_(None),
            ).all()
            for job in active_jobs:
                job.status = JobStatus.cancelled

        db.session.commit()

        return {"message": "User has been banned.", "user": user.to_dict()}

    @staticmethod
    def unban_user(user_id: int) -> Dict[str, Any]:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("not_found|User not found.")

        if not user.is_banned:
            raise ValueError("not_banned|User is not banned.")

        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None
        db.session.commit()

        return {"message": "User has been unbanned.", "user": user.to_dict()}

    @staticmethod
    def reject_booking(job_request_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        job = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
        if not job:
            raise ValueError("not_found|Job request not found.")

        if job.status in (JobStatus.completed, JobStatus.rejected):
            raise ValueError(
                "invalid_status|Cannot reject a completed or already rejected booking."
            )

        job.status = JobStatus.rejected
        db.session.commit()

        return {"message": "Booking has been rejected.", "job_request": job.to_dict()}

    @staticmethod
    def get_all_bookings(
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = JobRequest.query.filter(JobRequest.deleted_at.is_(None))

        if status_filter:
            try:
                status_enum = JobStatus(status_filter)
                query = query.filter_by(status=status_enum)
            except ValueError:
                valid = ", ".join([s.value for s in JobStatus])
                raise ValueError(f"invalid_status|status must be one of: {valid}.")

        if search:
            search_term = f"%{search}%"
            query = query.filter(JobRequest.title.ilike(search_term))

        query = query.order_by(JobRequest.created_at.desc())
        jobs = query.all()

        return {"job_requests": [j.to_dict() for j in jobs]}
