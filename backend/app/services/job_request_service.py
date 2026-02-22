from typing import Dict, Any, Optional, List
from datetime import datetime, date, time

from sqlalchemy import or_
from app.models import db, JobRequest, JobStatus, ServiceType


class JobRequestService:
    @staticmethod
    def create_job_request(end_user_id: int, data: dict) -> Dict[str, Any]:
        """
        Create a new job request
        """
        data = data or {}

        # Allowed fields for creation
        allowed = {
            "title", "description", "service_type", "location",
            "preferred_date", "preferred_time_start", "preferred_time_end",
        }
        updates = {k: data.get(k) for k in allowed if k in data}

        # Validate required fields
        if not updates.get("title"):
            raise ValueError("invalid_request|title is required.")
        if not updates.get("service_type"):
            raise ValueError("invalid_request|service_type is required.")
        if not updates.get("location", "").strip():
            raise ValueError("invalid_request|location is required.")
        if not updates.get("preferred_date"):
            raise ValueError("invalid_request|preferred_date is required.")

        # Validate service_type if provided
        if "service_type" in updates and updates["service_type"] is not None:
            try:
                updates["service_type"] = ServiceType(updates["service_type"])
            except Exception:
                valid = ", ".join([s.value for s in ServiceType])
                raise ValueError(f"invalid_service_type|service_type must be one of: {valid}.")

        # Validate preferred_date if provided
        if "preferred_date" in updates and updates["preferred_date"] is not None:
            try:
                if isinstance(updates["preferred_date"], str):
                    updates["preferred_date"] = datetime.strptime(
                        updates["preferred_date"], "%Y-%m-%d"
                    ).date()
            except (ValueError, TypeError):
                raise ValueError("invalid_date|preferred_date must be in YYYY-MM-DD format.")
            if updates["preferred_date"] < date.today():
                raise ValueError("invalid_date|preferred_date cannot be in the past.")

        # Validate preferred_time_start if provided
        if "preferred_time_start" in updates and updates["preferred_time_start"] is not None:
            try:
                if isinstance(updates["preferred_time_start"], str):
                    updates["preferred_time_start"] = datetime.strptime(
                        updates["preferred_time_start"], "%H:%M"
                    ).time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|preferred_time_start must be in HH:MM format.")
            # If the job is scheduled for today, start time cannot be in the past
            job_date = updates.get("preferred_date")
            if job_date == date.today() and updates["preferred_time_start"] < datetime.now().time():
                raise ValueError("invalid_time|preferred_time_start cannot be in the past.")

        # Validate preferred_time_end if provided
        if "preferred_time_end" in updates and updates["preferred_time_end"] is not None:
            try:
                if isinstance(updates["preferred_time_end"], str):
                    updates["preferred_time_end"] = datetime.strptime(
                        updates["preferred_time_end"], "%H:%M"
                    ).time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|preferred_time_end must be in HH:MM format.")

        # Validate time range (end must be strictly after start)
        start_time = updates.get("preferred_time_start")
        end_time = updates.get("preferred_time_end")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("invalid_time|preferred_time_end must be strictly after preferred_time_start.")

        # Create job request
        job_request = JobRequest(
            end_user_id=end_user_id,
            status=JobStatus.pending,
            **updates
        )
        db.session.add(job_request)
        db.session.commit()

        return {
            "message": "Job request created successfully.",
            "job_request": job_request.to_dict()
        }

    @staticmethod
    def update_job_request(
        job_request_id: int,
        user_id: int,
        role: str,
        data: dict
    ) -> Dict[str, Any]:
        """
        Update job request details
        """
        job_request = JobRequest.query.filter_by(id=job_request_id).first()
        if not job_request:
            raise ValueError("not_found|Job request not found.")

        # Only owner can update
        if job_request.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to update this job request.")

        # Cannot update cancelled or completed jobs
        if job_request.status in [JobStatus.completed, JobStatus.cancelled]:
            raise ValueError("invalid_status|Cannot update a completed or cancelled job request.")

        data = data or {}

        # Allowed fields for update
        allowed = {
            "title", "description", "service_type", "location",
            "preferred_date", "preferred_time_start", "preferred_time_end",
        }
        updates = {k: data.get(k) for k in allowed if k in data}

        # Validate that required fields are not being cleared
        if "service_type" in updates and not updates.get("service_type"):
            raise ValueError("invalid_request|service_type is required.")
        if "location" in updates and not (updates.get("location") or "").strip():
            raise ValueError("invalid_request|location is required.")
        if "preferred_date" in updates and not updates.get("preferred_date"):
            raise ValueError("invalid_request|preferred_date is required.")

        # Validate service_type if provided
        if "service_type" in updates and updates["service_type"] is not None:
            try:
                updates["service_type"] = ServiceType(updates["service_type"])
            except Exception:
                valid = ", ".join([s.value for s in ServiceType])
                raise ValueError(f"invalid_service_type|service_type must be one of: {valid}.")

        # Validate preferred_date if provided
        if "preferred_date" in updates and updates["preferred_date"] is not None:
            try:
                if isinstance(updates["preferred_date"], str):
                    updates["preferred_date"] = datetime.strptime(
                        updates["preferred_date"], "%Y-%m-%d"
                    ).date()
            except (ValueError, TypeError):
                raise ValueError("invalid_date|preferred_date must be in YYYY-MM-DD format.")
            if updates["preferred_date"] < date.today():
                raise ValueError("invalid_date|preferred_date cannot be in the past.")

        # Validate preferred_time_start if provided
        if "preferred_time_start" in updates and updates["preferred_time_start"] is not None:
            try:
                if isinstance(updates["preferred_time_start"], str):
                    updates["preferred_time_start"] = datetime.strptime(
                        updates["preferred_time_start"], "%H:%M"
                    ).time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|preferred_time_start must be in HH:MM format.")
            # Use the updated date if provided, otherwise fall back to the existing date
            job_date = updates.get("preferred_date", job_request.preferred_date)
            if job_date == date.today() and updates["preferred_time_start"] < datetime.now().time():
                raise ValueError("invalid_time|preferred_time_start cannot be in the past.")

        # Validate preferred_time_end if provided
        if "preferred_time_end" in updates and updates["preferred_time_end"] is not None:
            try:
                if isinstance(updates["preferred_time_end"], str):
                    updates["preferred_time_end"] = datetime.strptime(
                        updates["preferred_time_end"], "%H:%M"
                    ).time()
            except (ValueError, TypeError):
                raise ValueError("invalid_time|preferred_time_end must be in HH:MM format.")

        # Validate time range (end must be strictly after start)
        start_time = updates.get("preferred_time_start", job_request.preferred_time_start)
        end_time = updates.get("preferred_time_end", job_request.preferred_time_end)
        if start_time and end_time and end_time <= start_time:
            raise ValueError("invalid_time|preferred_time_end must be strictly after preferred_time_start.")

        # Apply updates
        for k, v in updates.items():
            setattr(job_request, k, v)

        db.session.commit()

        return {
            "message": "Job request updated successfully.",
            "job_request": job_request.to_dict()
        }

    @staticmethod
    def delete_job_request(job_request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """
        Delete a job request.
        Only the end user who created the request can delete it.
        """
        job_request = JobRequest.query.filter_by(id=job_request_id).first()
        if not job_request:
            raise ValueError("not_found|Job request not found.")

        # Only owner can delete
        if job_request.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to delete this job request.")

        # Cannot delete in_progress or completed jobs
        if job_request.status in [JobStatus.in_progress, JobStatus.completed]:
            raise ValueError(
                "invalid_status|Cannot delete a job request that is in progress or completed."
            )

        db.session.delete(job_request)
        db.session.commit()

        return {"message": "Job request deleted successfully."}

    @staticmethod
    def get_job_request(job_request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """
        Get a single job request by ID.
        End users can only view their own requests.
        Cleaners can view requests assigned to them or unassigned pending requests.
        """
        job_request = JobRequest.query.filter_by(id=job_request_id).first()
        if not job_request:
            raise ValueError("not_found|Job request not found.")

        # Check authorization
        if role == "end_user" and job_request.end_user_id != user_id:
            raise ValueError("forbidden|You are not authorized to view this job request.")
        if role == "cleaner":
            is_assigned_to_cleaner = job_request.cleaner_id == user_id
            is_open_pending = job_request.cleaner_id is None and job_request.status == JobStatus.pending
            if not is_assigned_to_cleaner and not is_open_pending:
                raise ValueError("forbidden|You are not authorized to view this job request.")

        return {"job_request": job_request.to_dict()}

    @staticmethod
    def get_job_requests(
        user_id: int,
        role: str,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get job requests based on user role.
        End users see their own requests.
        Cleaners see requests assigned to them.
        """
        if role == "end_user":
            query = JobRequest.query.filter_by(end_user_id=user_id)
        elif role == "cleaner":
            # Cleaners see: jobs assigned to them OR unassigned pending jobs
            query = JobRequest.query.filter(
                or_(
                    JobRequest.cleaner_id == user_id,
                    (JobRequest.cleaner_id == None) & (JobRequest.status == JobStatus.pending)
                )
            )
        else:
            # Administrator can see all
            query = JobRequest.query

        # Filter by status if provided
        if status:
            try:
                status_enum = JobStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                valid = ", ".join([s.value for s in JobStatus])
                raise ValueError(f"invalid_status|status must be one of: {valid}.")

        # Order by most recent first
        query = query.order_by(JobRequest.created_at.desc())
        job_requests = query.all()

        return {"job_requests": [jr.to_dict() for jr in job_requests]}

    @staticmethod
    def update_job_status(
        job_request_id: int,
        user_id: int,
        role: str,
        new_status: str
    ) -> Dict[str, Any]:
        """
        Update job request status (pending, confirmed, in_progress, completed, cancelled).
        - End users can cancel their pending/confirmed requests
        - Cleaners can confirm, start, and complete assigned jobs
        """
        job_request = JobRequest.query.filter_by(id=job_request_id).first()
        if not job_request:
            raise ValueError("not_found|Job request not found.")

        try:
            new_status_enum = JobStatus(new_status)
        except ValueError:
            valid = ", ".join([s.value for s in JobStatus])
            raise ValueError(f"invalid_status|status must be one of: {valid}.")

        current_status = job_request.status

        # End user can only cancel their own requests once a cleaner has been assigned
        if role == "end_user":
            if job_request.end_user_id != user_id:
                raise ValueError("forbidden|You are not authorized to update this job request.")
            if new_status_enum != JobStatus.cancelled:
                raise ValueError("forbidden|End users can only cancel job requests.")
            if job_request.cleaner_id is None:
                raise ValueError(
                    "forbidden|Cannot cancel a job request that has not been assigned to a cleaner."
                )
            if current_status not in [JobStatus.pending, JobStatus.confirmed]:
                raise ValueError(
                    "invalid_status|Can only cancel pending or confirmed job requests."
                )

        # Cleaner status transitions
        elif role == "cleaner":
            is_unassigned_pending = (
                job_request.cleaner_id is None and current_status == JobStatus.pending
            )

            if is_unassigned_pending:
                # Cleaner is claiming an open job — only allowed transition is confirmed
                if new_status_enum != JobStatus.confirmed:
                    raise ValueError(
                        "invalid_status|Can only confirm (accept) an unassigned pending job."
                    )
                job_request.cleaner_id = user_id
            elif job_request.cleaner_id != user_id:
                raise ValueError("forbidden|You are not authorized to update this job request.")
            else:
                valid_transitions = {
                    JobStatus.confirmed: [JobStatus.in_progress, JobStatus.cancelled],
                    JobStatus.in_progress: [JobStatus.completed],
                }

                allowed_statuses = valid_transitions.get(current_status, [])
                if new_status_enum not in allowed_statuses:
                    allowed_values = ", ".join([s.value for s in allowed_statuses])
                    raise ValueError(
                        f"invalid_status|Cannot transition from {current_status.value} to {new_status}. "
                        f"Allowed: {allowed_values}."
                    )

        job_request.status = new_status_enum
        db.session.commit()

        return {
            "message": f"Job request status updated to {new_status}.",
            "job_request": job_request.to_dict()
        }

