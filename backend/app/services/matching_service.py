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
    def build_score_expression(self, job: JobRequest):
        """Return a SQLAlchemy expression used to rank matching cleaners."""

    @abstractmethod
    def score_cleaner(self, job: JobRequest, user: User, profile: CleanerProfile) -> float:
        """Return the in-memory score for a cleaner profile."""

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

    @classmethod
    def _availability_level_expression(cls, job: JobRequest):
        """
        Shared raw component for SQL scoring.
        2 = fully available, 1 = no availability configured, 0 = unavailable.
        """
        return case(
            (cls._matching_availability_exists(job), 2),
            (~cls._has_any_availability(), 1),
            else_=0,
        )

    @staticmethod
    def _experience_years_expression():
        return func.coalesce(CleanerProfile.years_experience, 0)

    @staticmethod
    def _rate_band_expression():
        """
        Shared raw component for SQL scoring.
        4 = lowest price band, 1 = highest non-null price band, 0 = missing rate.
        """
        return case(
            (CleanerProfile.hourly_rate <= 20, 4),
            (CleanerProfile.hourly_rate <= 35, 3),
            (CleanerProfile.hourly_rate <= 50, 2),
            (CleanerProfile.hourly_rate.isnot(None), 1),
            else_=0,
        )

    @staticmethod
    def _rate_band(profile: CleanerProfile) -> int:
        if not profile.hourly_rate:
            return 0

        rate = float(profile.hourly_rate)
        if rate <= 20:
            return 4
        if rate <= 35:
            return 3
        if rate <= 50:
            return 2
        return 1

    @staticmethod
    def _experience_years(profile: CleanerProfile) -> int:
        return profile.years_experience or 0

    @staticmethod
    def _availability_level(job: JobRequest, profile: CleanerProfile) -> int:
        availability_slots = profile.availability
        if not availability_slots:
            return 1

        for slot in availability_slots:
            if not (slot.start_date <= job.preferred_date <= slot.end_date):
                continue

            if slot.start_time is None and slot.end_time is None:
                return 2

            if job.preferred_time_start is None:
                return 2

            time_ok = True
            if slot.start_time and job.preferred_time_start:
                if job.preferred_time_start < slot.start_time:
                    time_ok = False
            if slot.end_time and job.preferred_time_end:
                if job.preferred_time_end > slot.end_time:
                    time_ok = False

            if time_ok:
                return 2

        return 0

    @staticmethod
    def _service_type_matches(job: JobRequest, profile: CleanerProfile) -> bool:
        return profile.service_type == job.service_type


class DefaultMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy.
    This is the default implementation and preserves the original matching
    behaviour used by the application.
    """

    name = "default"

    def build_score_expression(self, job: JobRequest):
        availability_level = self._availability_level_expression(job)
        experience_years = self._experience_years_expression()
        rate_band = self._rate_band_expression()

        availability_score = case(
            (availability_level == 2, 30),
            (availability_level == 1, 15),
            else_=0,
        )
        experience_score = func.least(experience_years * 2, 20)
        rate_score = case(
            (rate_band == 4, 10),
            (rate_band == 3, 7),
            (rate_band == 2, 4),
            (rate_band == 1, 1),
            else_=0,
        )

        return (
            literal(40)
            + availability_score
            + experience_score
            + rate_score
        ).label("score")

    def score_cleaner(self, job: JobRequest, user: User, profile: CleanerProfile) -> float:
        if not self._service_type_matches(job, profile):
            return 0.0

        availability_level = self._availability_level(job, profile)
        availability_score = 30.0 if availability_level == 2 else 15.0 if availability_level == 1 else 0.0

        experience_years = self._experience_years(profile)
        experience_score = float(min(experience_years * 2, 20))

        rate_band = self._rate_band(profile)
        rate_score = {4: 10.0, 3: 7.0, 2: 4.0, 1: 1.0}.get(rate_band, 0.0)

        return 40.0 + availability_score + experience_score + rate_score


class LowestPriceMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy.
    This implementation prioritizes cheaper cleaners over more experienced ones.
    """

    name = "lowest_price"

    def build_score_expression(self, job: JobRequest):
        availability_level = self._availability_level_expression(job)
        experience_years = self._experience_years_expression()
        rate_band = self._rate_band_expression()

        availability_score = case(
            (availability_level == 2, 30),
            (availability_level == 1, 15),
            else_=0,
        )
        experience_score = func.least(experience_years, 10)
        rate_priority = case(
            (rate_band == 4, 25),
            (rate_band == 3, 18),
            (rate_band == 2, 10),
            (rate_band == 1, 3),
            else_=0,
        )

        return (
            literal(30)
            + availability_score
            + experience_score
            + rate_priority
        ).label("score")

    def score_cleaner(self, job: JobRequest, user: User, profile: CleanerProfile) -> float:
        if not self._service_type_matches(job, profile):
            return 0.0

        availability_level = self._availability_level(job, profile)
        availability_score = 30.0 if availability_level == 2 else 15.0 if availability_level == 1 else 0.0

        experience_score = float(min(self._experience_years(profile), 10))
        rate_score = {4: 25.0, 3: 18.0, 2: 10.0, 1: 3.0}.get(self._rate_band(profile), 0.0)

        return 30.0 + availability_score + experience_score + rate_score


class HighestExperienceMatchingStrategy(CleanerMatchingStrategy):
    """
    Concrete strategy.
    This implementation prioritizes more experienced cleaners over cheaper ones.
    """

    name = "highest_experience"

    def build_score_expression(self, job: JobRequest):
        availability_level = self._availability_level_expression(job)
        experience_years = self._experience_years_expression()
        rate_band = self._rate_band_expression()

        availability_score = case(
            (availability_level == 2, 30),
            (availability_level == 1, 15),
            else_=0,
        )
        exp_priority = func.least(experience_years * 4, 40)
        rate_score = case(
            (rate_band == 4, 10),
            (rate_band == 3, 7),
            (rate_band == 2, 4),
            (rate_band == 1, 1),
            else_=0,
        )

        return (
            literal(30)
            + availability_score
            + exp_priority
            + rate_score
        ).label("score")

    def score_cleaner(self, job: JobRequest, user: User, profile: CleanerProfile) -> float:
        if not self._service_type_matches(job, profile):
            return 0.0

        availability_level = self._availability_level(job, profile)
        availability_score = 30.0 if availability_level == 2 else 15.0 if availability_level == 1 else 0.0

        exp_score = float(min(self._experience_years(profile) * 4, 40))
        rate_score = {4: 10.0, 3: 7.0, 2: 4.0, 1: 1.0}.get(self._rate_band(profile), 0.0)

        return 30.0 + availability_score + exp_score + rate_score


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
        return scored

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
        score_expr = strategy.build_score_expression(job)
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

    @classmethod
    def _score_cleaner(cls, job: JobRequest, user: User, profile: CleanerProfile) -> float:
        """
        Compatibility wrapper for existing tests and internal callers.
        This delegates to the default concrete strategy via the context.
        """
        strategy = cls._resolve_strategy()
        return strategy.score_cleaner(job, user, profile)
