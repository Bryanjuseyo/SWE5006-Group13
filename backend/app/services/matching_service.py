from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, exists, func, or_, literal
from app.models import (
    db, User, UserRole, UserProfile, JobRequest, JobStatus,
    CleanerProfile, CleanerAvailability, PRIORITY_WINDOW_HOURS,
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

        booked_job_filters = [
            JobRequest.cleaner_id == User.id,
            JobRequest.deleted_at.is_(None),
            JobRequest.status.in_([
                JobStatus.confirmed,
                JobStatus.in_progress,
            ]),
            JobRequest.preferred_date == job.preferred_date,
            JobRequest.id != job.id,
        ]

        if job.preferred_time_start and job.preferred_time_end:
            booked_job_filters.append(
                or_(
                    JobRequest.preferred_time_start.is_(None),
                    and_(
                        JobRequest.preferred_time_start < job.preferred_time_end,
                        JobRequest.preferred_time_end > job.preferred_time_start,
                    ),
                )
            )

        booked_overlap_exists = exists().where(and_(*booked_job_filters))

        availability_date_filters = [
            CleanerAvailability.cleaner_profile_id == CleanerProfile.id,
            CleanerAvailability.start_date <= job.preferred_date,
            CleanerAvailability.end_date >= job.preferred_date,
        ]
        has_any_availability = exists().where(
            CleanerAvailability.cleaner_profile_id == CleanerProfile.id
        )

        if job.preferred_time_start is None:
            matching_availability_exists = exists().where(and_(*availability_date_filters))
        else:
            matching_time_filters = list(availability_date_filters)
            matching_time_filters.append(
                or_(
                    and_(
                        CleanerAvailability.start_time.is_(None),
                        CleanerAvailability.end_time.is_(None),
                    ),
                    and_(
                        or_(
                            CleanerAvailability.start_time.is_(None),
                            CleanerAvailability.start_time <= job.preferred_time_start,
                        ),
                        or_(
                            CleanerAvailability.end_time.is_(None),
                            job.preferred_time_end is None,
                            CleanerAvailability.end_time >= job.preferred_time_end,
                        ),
                    ),
                )
            )
            matching_availability_exists = exists().where(and_(*matching_time_filters))

        availability_score = case(
            (matching_availability_exists, 30),
            (~has_any_availability, 15),
            else_=0,
        )
        experience_score = func.least(
            func.coalesce(CleanerProfile.years_experience, 0) * 2,
            20,
        )
        rate_score = case(
            (CleanerProfile.hourly_rate <= 20, 10),
            (CleanerProfile.hourly_rate <= 35, 7),
            (CleanerProfile.hourly_rate <= 50, 4),
            (CleanerProfile.hourly_rate.isnot(None), 1),
            else_=0,
        )
        score_expr = (
            literal(40)
            + availability_score
            + experience_score
            + rate_score
        ).label("score")

        matches = (
            db.session.query(
                User.id.label("cleaner_id"),
                User.email.label("email"),
                UserProfile.first_name.label("first_name"),
                UserProfile.last_name.label("last_name"),
                CleanerProfile.service_type.label("service_type"),
                CleanerProfile.hourly_rate.label("hourly_rate"),
                CleanerProfile.years_experience.label("years_experience"),
                score_expr,
            )
            .join(CleanerProfile, User.id == CleanerProfile.user_id)
            .outerjoin(UserProfile, User.id == UserProfile.user_id)
            .filter(
                User.role == UserRole.cleaner,
                User.is_banned.is_(False),
                CleanerProfile.service_type == job.service_type,
                ~booked_overlap_exists,
            )
            .order_by(score_expr.desc())
            .limit(5)
            .all()
        )

        scored: List[Dict[str, Any]] = []
        for match in matches:
            if match.score <= 0:
                continue

            if match.first_name and match.last_name:
                name = f"{match.first_name} {match.last_name}"
            else:
                name = match.email

            scored.append({
                "cleaner_id": match.cleaner_id,
                "email": match.email,
                "name": name,
                "service_type": match.service_type.value,
                "hourly_rate": float(match.hourly_rate) if match.hourly_rate else None,
                "years_experience": match.years_experience,
                "score": float(match.score),
            })

        return {
            "job_request_id": job.id,
            "matches": scored,
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
            # No availability set - assume available (+15 partial credit)
            score += 15

        # Experience bonus (up to +20)
        exp = profile.years_experience or 0
        score += min(exp * 2, 20)

        # Rate competitiveness bonus (up to +10 - lower rate gets higher score)
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
