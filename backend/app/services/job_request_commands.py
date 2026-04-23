from abc import ABC, abstractmethod
from typing import Any, Dict


class JobRequestCommand(ABC):
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        raise NotImplementedError


class JobRequestCommandInvoker:
    @staticmethod
    def execute(command: JobRequestCommand) -> Dict[str, Any]:
        return command.execute()


class CreateJobRequestCommand(JobRequestCommand):
    def __init__(self, end_user_id: int, data: dict):
        self.end_user_id = end_user_id
        self.data = data

    def execute(self) -> Dict[str, Any]:
        from app.services.job_request_service import JobRequestService

        return JobRequestService._create_job_request(self.end_user_id, self.data)


class UpdateJobRequestCommand(JobRequestCommand):
    def __init__(self, job_request_id: int, user_id: int, role: str, data: dict):
        self.job_request_id = job_request_id
        self.user_id = user_id
        self.role = role
        self.data = data

    def execute(self) -> Dict[str, Any]:
        from app.services.job_request_service import JobRequestService

        return JobRequestService._update_job_request(
            self.job_request_id,
            self.user_id,
            self.role,
            self.data,
        )


class DeleteJobRequestCommand(JobRequestCommand):
    def __init__(self, job_request_id: int, user_id: int, role: str):
        self.job_request_id = job_request_id
        self.user_id = user_id
        self.role = role

    def execute(self) -> Dict[str, Any]:
        from app.services.job_request_service import JobRequestService

        return JobRequestService._delete_job_request(
            self.job_request_id,
            self.user_id,
            self.role,
        )


class UpdateJobStatusCommand(JobRequestCommand):
    def __init__(self, job_request_id: int, user_id: int, role: str, new_status: str):
        self.job_request_id = job_request_id
        self.user_id = user_id
        self.role = role
        self.new_status = new_status

    def execute(self) -> Dict[str, Any]:
        from app.services.job_request_service import JobRequestService

        return JobRequestService._update_job_status(
            self.job_request_id,
            self.user_id,
            self.role,
            self.new_status,
        )
