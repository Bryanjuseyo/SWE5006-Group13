from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from app.models import (
    db, User, UserRole, UserProfile, JobRequest, JobStatus,
    CleanerProfile, CleanerAvailability, ServiceType, PRIORITY_WINDOW_HOURS,
)


class MatchingService:
    """
    Automated cleaner matching.
    Scores cleaners based on: service type match, availability overlap,
    experience, and hourly rate.
    """

    @staticmethod
    def find_matching_cleaners(job_request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        job = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
        if not job:
            raise ValueError("not_found|Job request not found.")

        # Only owner or admin can request matching
        if role == "end_user" and job.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to match cleaners for this job.")

        if job.status != JobStatus.pending:
            raise ValueError("invalid_status|Can only match cleaners for pending jobs.")

        # Get all active (non-banned) cleaners with profiles
        cleaners = (
            db.session.query(User, CleanerProfile)
            .join(CleanerProfile, User.id == CleanerProfile.user_id)
            .filter(
                User.role == UserRole.cleaner,
                User.is_banned.is_(False),
            )
            .all()
        )

        scored: List[Dict[str, Any]] = []
        for user, profile in cleaners:
            score = MatchingService._score_cleaner(job, user, profile)
            if score > 0:
                user_profile = UserProfile.query.filter_by(user_id=user.id).first()
                scored.append({
                    "cleaner_id": user.id,
                    "email": user.email,
                    "name": (
                        f"{user_profile.first_name} {user_profile.last_name}"
                        if user_profile else user.email
                    ),
                    "service_type": profile.service_type.value,
                    "hourly_rate": float(profile.hourly_rate) if profile.hourly_rate else None,
                    "years_experience": profile.years_experience,
                    "score": score,
                })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Return top 5 matches
        return {
            "job_request_id": job.id,
            "matches": scored[:5],
        }

    @staticmethod
    def auto_assign_cleaner(job_request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """Auto-assign the best matching cleaner to a pending job."""
        result = MatchingService.find_matching_cleaners(job_request_id, user_id, role)

        if not result["matches"]:
            raise ValueError("no_match|No suitable cleaners found for this job.")

        best = result["matches"][0]
        job = JobRequest.query.get(job_request_id)
        job.cleaner_id = best["cleaner_id"]
        job.priority_window_end = datetime.now(timezone.utc) + timedelta(hours=PRIORITY_WINDOW_HOURS)
        db.session.commit()

        return {
            "message": f"Cleaner {best['name']} has been assigned to the job.",
            "job_request": job.to_dict(),
            "assigned_cleaner": best,
        }

    @staticmethod
    def _score_cleaner(job: JobRequest, user: User, profile: CleanerProfile) -> float:
        score = 0.0

        # Service type match (must match, otherwise score is 0)
        if profile.service_type != job.service_type:
            return 0.0

        score += 40  # Base score for service type match

        # Availability check (+30 if available on the job date/time)
        availability_slots = profile.availability
        if availability_slots:
            for slot in availability_slots:
                if not (slot.start_date <= job.preferred_date <= slot.end_date):
                    continue

                # Date matches
                if slot.start_time is None and slot.end_time is None:
                    score += 30
                    break

                if job.preferred_time_start is None:
                    score += 30
                    break

                time_ok = True
                if slot.start_time and job.preferred_time_start:
                    if job.preferred_time_start < slot.start_time:
                        time_ok = False
                if slot.end_time and job.preferred_time_end:
                    if job.preferred_time_end > slot.end_time:
                        time_ok = False

                if time_ok:
                    score += 30
                    break
        else:
            # No availability set — assume available (+15 partial credit)
            score += 15

        # Experience bonus (up to +20)
        exp = profile.years_experience or 0
        score += min(exp * 2, 20)

        # Rate competitiveness bonus (up to +10 — lower rate gets higher score)
        if profile.hourly_rate:
            rate = float(profile.hourly_rate)
            if rate <= 20:
                score += 10
            elif rate <= 35:
                score += 7
            elif rate <= 50:
                score += 4
            else:
                score += 1

        return score
