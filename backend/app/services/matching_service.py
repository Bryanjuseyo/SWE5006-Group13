from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import and_, case, exists, func, literal, or_

from app.models import (
    PRIORITY_WINDOW_HOURS,
    CleanerAvailability,
    CleanerProfile,
    JobRequest,
    JobStatus,
    User,
    UserProfile,
    UserRole,
    db,
)


class CleanerMatchingStrategy(ABC):
    """
    Strategy interface.
    All concrete matching strategies must implement this contract so the
    context can swap ranking behaviour without changing the workflow.
    """

    name = "base"

    @abstractmethod
    def build_order_by(self, job: JobRequest):
        """Return SQLAlchemy order expressions for this strategy."""

    @staticmethod
    def _matching_availability_exists(job: JobRequest):
        availability_date_filters = [
            CleanerAvailability.cleaner_profile_id == CleanerProfile.id,
            CleanerAvailability.start_date <= job.preferred_date,
            CleanerAvailability.end_date >= job.preferred_date,
        ]

        if job.preferred_time_start is None:
            return exists().where(and_(*availability_date_filters))

        end_time_conditions = [CleanerAvailability.end_time.is_(None)]
        if job.preferred_time_end is not None:
            end_time_conditions.append(
                CleanerAvailability.end_time >= job.preferred_time_end,
            )

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
                    or_(*end_time_conditions),
                ),
            )
        )
        return exists().where(and_(*matching_time_filters))

    @staticmethod
    def _has_any_availability():
        return exists().where(CleanerAvailability.cleaner_profile_id == CleanerProfile.id)

    @staticmethod
    def _experience_years_expression():
        return func.coalesce(CleanerProfile.years_experience, 0)

    @staticmethod
    def _hourly_rate_nulls_last_expression():
        return case((CleanerProfile.hourly_rate.is_(None), 1), else_=0)

    @classmethod
    def _availability_is_eligible_expression(cls, job: JobRequest):
        return or_(cls._matching_availability_exists(job), ~cls._has_any_availability())


class DefaultMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy. Uses a balanced formula: 50% cleaner experience and
    50% pricing.
    """

    name = "default"

    @staticmethod
    def _experience_score_expression():
        return func.least(DefaultMatchingStrategy._experience_years_expression() * 10, 100)

    @staticmethod
    def _pricing_score_expression():
        return case(
            (and_(CleanerProfile.hourly_rate >= 0, CleanerProfile.hourly_rate <= 20), 100),
            (
                and_(CleanerProfile.hourly_rate > 20, CleanerProfile.hourly_rate < 80),
                literal(100) - ((CleanerProfile.hourly_rate - literal(20)) * literal(100 / 60)),
            ),
            else_=0,
        )

    def _ranking_expression(self):
        experience_score = self._experience_score_expression()
        pricing_score = self._pricing_score_expression()
        return (experience_score * literal(0.5) + pricing_score * literal(0.5)).label("ranking_score")

    def build_order_by(self, job: JobRequest):
        return [
            self._ranking_expression().desc(),
            self._hourly_rate_nulls_last_expression().asc(),
            CleanerProfile.hourly_rate.asc(),
            User.id.asc(),
        ]


class LowestPriceMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy. Chooses the cheapest available cleaner first, using
    experience only as a tie-breaker.
    """

    name = "lowest_price"

    def build_order_by(self, job: JobRequest):
        return [
            self._hourly_rate_nulls_last_expression().asc(),
            CleanerProfile.hourly_rate.asc(),
            self._experience_years_expression().desc(),
            User.id.asc(),
        ]


class HighestExperienceMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy. Chooses the most experienced available cleaner first,
    using hourly rate only as a tie-breaker.
    """

    name = "highest_experience"

    def build_order_by(self, job: JobRequest):
        return [
            self._experience_years_expression().desc(),
            self._hourly_rate_nulls_last_expression().asc(),
            CleanerProfile.hourly_rate.asc(),
            User.id.asc(),
        ]


class MatchingService:
    """
    Context.
    MatchingService owns the overall matching workflow and delegates ranking
    behaviour to a CleanerMatchingStrategy implementation.
    """

    _strategies: Dict[str, CleanerMatchingStrategy] = {
        DefaultMatchingStrategy.name: DefaultMatchingStrategy(),
        LowestPriceMatchingStrategy.name: LowestPriceMatchingStrategy(),
        HighestExperienceMatchingStrategy.name: HighestExperienceMatchingStrategy(),
    }
    _default_strategy_name = DefaultMatchingStrategy.name

    @classmethod
    def register_strategy(cls, strategy: CleanerMatchingStrategy):
        """Register a new concrete strategy with the context."""
        cls._strategies[strategy.name] = strategy

    @classmethod
    def _resolve_strategy(cls, strategy_name: str | None = None) -> CleanerMatchingStrategy:
        """Select the concrete strategy to be used by the context."""
        resolved_name = strategy_name or cls._default_strategy_name
        strategy = cls._strategies.get(resolved_name)
        if not strategy:
            valid = ", ".join(sorted(cls._strategies.keys()))
            raise ValueError(f"invalid_strategy|strategy must be one of: {valid}.")
        return strategy

    @staticmethod
    def _load_pending_job(job_request_id: int, user_id: int, role: str) -> JobRequest:
        job = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
        if not job:
            raise ValueError("not_found|Job request not found.")

        if role == "end_user" and job.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to match cleaners for this job.")

        if job.status != JobStatus.pending:
            raise ValueError("invalid_status|Can only match cleaners for pending jobs.")

        return job

    @staticmethod
    def _build_booked_overlap_exists(job: JobRequest):
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

        return exists().where(and_(*booked_job_filters))

    @staticmethod
    def _format_matches(matches) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for match in matches:
            if match.first_name and match.last_name:
                name = f"{match.first_name} {match.last_name}"
            else:
                name = match.email

            formatted.append({
                "cleaner_id": match.cleaner_id,
                "email": match.email,
                "name": name,
                "service_type": match.service_type.value,
                "hourly_rate": float(match.hourly_rate) if match.hourly_rate else None,
                "years_experience": match.years_experience,
            })
        return formatted

    @classmethod
    def find_matching_cleaners(
        cls,
        job_request_id: int,
        user_id: int,
        role: str,
        strategy_name: str | None = None,
    ) -> Dict[str, Any]:
        """
        Context operation.
        The workflow stays the same, but the ranking logic is delegated to the
        selected strategy implementation.
        """
        job = cls._load_pending_job(job_request_id, user_id, role)
        strategy = cls._resolve_strategy(strategy_name)
        availability_is_eligible = strategy._availability_is_eligible_expression(job)
        booked_overlap_exists = cls._build_booked_overlap_exists(job)

        matches = (
            db.session.query(
                User.id.label("cleaner_id"),
                User.email.label("email"),
                UserProfile.first_name.label("first_name"),
                UserProfile.last_name.label("last_name"),
                CleanerProfile.service_type.label("service_type"),
                CleanerProfile.hourly_rate.label("hourly_rate"),
                CleanerProfile.years_experience.label("years_experience"),
            )
            .join(CleanerProfile, User.id == CleanerProfile.user_id)
            .outerjoin(UserProfile, User.id == UserProfile.user_id)
            .filter(
                User.role == UserRole.cleaner,
                User.is_banned.is_(False),
                CleanerProfile.service_type == job.service_type,
                availability_is_eligible,
                ~booked_overlap_exists,
            )
            .order_by(*strategy.build_order_by(job))
            .limit(5)
            .all()
        )

        return {
            "job_request_id": job.id,
            "strategy": strategy.name,
            "matches": cls._format_matches(matches),
        }

    @classmethod
    def auto_assign_cleaner(
        cls,
        job_request_id: int,
        user_id: int,
        role: str,
        strategy_name: str | None = None,
    ) -> Dict[str, Any]:
        """Auto-assign the best matching cleaner to a pending job."""
        result = cls.find_matching_cleaners(job_request_id, user_id, role, strategy_name)

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
            "strategy": result["strategy"],
        }
