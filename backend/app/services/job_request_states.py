from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models import JobRequest, JobStatus


@dataclass
class JobStatusTransition:
    status: JobStatus | None = None
    message: str | None = None
    return_immediately: bool = False


class BaseJobRequestState(ABC):
    status: JobStatus

    def transition(
        self,
        job_request: JobRequest,
        user_id: int,
        role: str,
        new_status: JobStatus,
    ) -> JobStatusTransition:
        if role == "end_user":
            return self._transition_end_user(job_request, user_id, new_status)
        if role == "cleaner":
            return self._transition_cleaner(job_request, user_id, new_status)
        raise ValueError("forbidden|You are not authorized to update this job request.")

    @abstractmethod
    def _transition_end_user(
        self,
        job_request: JobRequest,
        user_id: int,
        new_status: JobStatus,
    ) -> JobStatusTransition:
        raise NotImplementedError

    @abstractmethod
    def _transition_cleaner(
        self,
        job_request: JobRequest,
        user_id: int,
        new_status: JobStatus,
    ) -> JobStatusTransition:
        raise NotImplementedError

    @staticmethod
    def _ensure_end_user_owner(job_request: JobRequest, user_id: int):
        if job_request.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to update this job request.")

    @staticmethod
    def _ensure_cleaner_assigned(job_request: JobRequest, user_id: int):
        if job_request.cleaner_id != user_id:
            raise ValueError("forbidden|You are not authorized to update this job request.")

    @staticmethod
    def _raise_end_user_forbidden():
        raise ValueError("forbidden|End users can only cancel or confirm completion of job requests.")

    @staticmethod
    def _raise_cancel_not_assigned():
        raise ValueError("forbidden|Cannot cancel a job request that has not been assigned to a cleaner.")

    @staticmethod
    def _raise_cancel_invalid():
        raise ValueError("invalid_status|Can only cancel pending or confirmed job requests.")

    @staticmethod
    def _raise_completion_invalid():
        raise ValueError(
            "invalid_status|Can only confirm completion after the cleaner has marked the job as done."
        )

    def _raise_invalid_transition(self, current_status: JobStatus, new_status: JobStatus, allowed_statuses: list[JobStatus]):
        allowed_values = ", ".join([status.value for status in allowed_statuses])
        raise ValueError(
            f"invalid_status|Cannot transition from {current_status.value} to {new_status.value}. "
            f"Allowed: {allowed_values}."
        )


class PendingJobRequestState(BaseJobRequestState):
    status = JobStatus.pending

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)

        if new_status == JobStatus.cancelled:
            if job_request.cleaner_id is None:
                self._raise_cancel_not_assigned()
            return JobStatusTransition(status=JobStatus.cancelled)

        if new_status == JobStatus.completed:
            self._raise_completion_invalid()

        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        if new_status == JobStatus.cancelled:
            if job_request.cleaner_id == user_id:
                job_request.cleaner_id = None
                job_request.priority_window_end = None
                return JobStatusTransition(
                    message="You have declined this job. It is now open to all cleaners.",
                    return_immediately=True,
                )
            raise ValueError("forbidden|You are not authorized to decline this job request.")

        if new_status != JobStatus.confirmed:
            raise ValueError("invalid_status|Can only confirm (accept) a pending job.")

        job_request.cleaner_id = user_id
        job_request.priority_window_end = None
        return JobStatusTransition(status=JobStatus.confirmed)


class ConfirmedJobRequestState(BaseJobRequestState):
    status = JobStatus.confirmed

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)

        if new_status == JobStatus.cancelled:
            if job_request.cleaner_id is None:
                self._raise_cancel_not_assigned()
            return JobStatusTransition(status=JobStatus.cancelled)

        if new_status == JobStatus.completed:
            self._raise_completion_invalid()

        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_cleaner_assigned(job_request, user_id)
        allowed = [JobStatus.in_progress, JobStatus.cancelled]
        if new_status not in allowed:
            self._raise_invalid_transition(job_request.status, new_status, allowed)
        return JobStatusTransition(status=new_status)


class InProgressJobRequestState(BaseJobRequestState):
    status = JobStatus.in_progress

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)

        if new_status == JobStatus.cancelled:
            self._raise_cancel_invalid()
        if new_status == JobStatus.completed:
            self._raise_completion_invalid()

        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_cleaner_assigned(job_request, user_id)
        allowed = [JobStatus.cleaner_completed]
        if new_status not in allowed:
            self._raise_invalid_transition(job_request.status, new_status, allowed)
        return JobStatusTransition(status=new_status)


class CleanerCompletedJobRequestState(BaseJobRequestState):
    status = JobStatus.cleaner_completed

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)

        if new_status == JobStatus.completed:
            return JobStatusTransition(status=JobStatus.completed)
        if new_status == JobStatus.cancelled:
            self._raise_cancel_invalid()

        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_cleaner_assigned(job_request, user_id)
        self._raise_invalid_transition(job_request.status, new_status, [])


class CompletedJobRequestState(BaseJobRequestState):
    status = JobStatus.completed

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)
        if new_status == JobStatus.cancelled:
            self._raise_cancel_invalid()
        if new_status == JobStatus.completed:
            self._raise_completion_invalid()
        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_cleaner_assigned(job_request, user_id)
        self._raise_invalid_transition(job_request.status, new_status, [])


class CancelledJobRequestState(BaseJobRequestState):
    status = JobStatus.cancelled

    def _transition_end_user(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_end_user_owner(job_request, user_id)
        if new_status == JobStatus.cancelled:
            self._raise_cancel_invalid()
        if new_status == JobStatus.completed:
            self._raise_completion_invalid()
        self._raise_end_user_forbidden()

    def _transition_cleaner(self, job_request: JobRequest, user_id: int, new_status: JobStatus) -> JobStatusTransition:
        self._ensure_cleaner_assigned(job_request, user_id)
        self._raise_invalid_transition(job_request.status, new_status, [])


class JobRequestStateFactory:
    _states = {
        PendingJobRequestState.status: PendingJobRequestState(),
        ConfirmedJobRequestState.status: ConfirmedJobRequestState(),
        InProgressJobRequestState.status: InProgressJobRequestState(),
        CleanerCompletedJobRequestState.status: CleanerCompletedJobRequestState(),
        CompletedJobRequestState.status: CompletedJobRequestState(),
        CancelledJobRequestState.status: CancelledJobRequestState(),
    }

    @classmethod
    def get_state(cls, status: JobStatus) -> BaseJobRequestState:
        state = cls._states.get(status)
        if not state:
            raise ValueError(f"invalid_status|Unsupported job request state: {status.value}.")
        return state
