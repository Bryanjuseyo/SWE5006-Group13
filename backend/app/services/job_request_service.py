from typing import Dict, Any, Optional
from datetime import datetime, date, timezone

from sqlalchemy import or_
from app.models import db, JobRequest, JobStatus, ServiceType, User, UserRole, CleanerProfile


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
            "cleaner_id",
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

        # Validate cleaner
        if "cleaner_id" in updates:
            updates["cleaner_id"] = JobRequestService._validate_cleaner_id(updates.get("cleaner_id"))

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
        job_request = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
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
            "cleaner_id",
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
        
        # Validate cleaner
        if "cleaner_id" in updates:
            if job_request.status != JobStatus.pending:
                raise ValueError("invalid_status|Cannot change preferred cleaner unless job is pending.")
            updates["cleaner_id"] = JobRequestService._validate_cleaner_id(updates.get("cleaner_id"))

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
        job_request = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
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

        job_request.deleted_at = datetime.now(timezone.utc)
        db.session.commit()

        return {"message": "Job request deleted successfully."}

    @staticmethod
    def get_job_request(job_request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """
        Get a single job request by ID.
        End users can only view their own requests.
        Cleaners can view requests assigned to them or unassigned pending requests.
        """
        job_request = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
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
            # Filter open jobs by the cleaner's service_type
            cleaner_profile = CleanerProfile.query.filter_by(user_id=user_id).first()
            cleaner_service_type = cleaner_profile.service_type if cleaner_profile else None

            if cleaner_service_type:
                open_job_filter = (
                    JobRequest.cleaner_id.is_(None) &
                    (JobRequest.status == JobStatus.pending) &
                    (JobRequest.service_type == cleaner_service_type)
                )
            else:
                # No profile set — show no open jobs, only assigned ones
                open_job_filter = (JobRequest.cleaner_id == user_id) & (False == True)

            query = JobRequest.query.filter(
                or_(
                    JobRequest.cleaner_id == user_id,
                    open_job_filter,
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

        # Exclude soft-deleted records
        query = query.filter(JobRequest.deleted_at.is_(None))

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
        job_request = JobRequest.query.filter_by(id=job_request_id).filter(
            JobRequest.deleted_at.is_(None)
        ).first()
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
            is_open_pending = current_status == JobStatus.pending

            if is_open_pending:
                # Any cleaner can claim a pending job (preferred cleaner is a soft hint)
                if new_status_enum != JobStatus.confirmed:
                    raise ValueError(
                        "invalid_status|Can only confirm (accept) a pending job."
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
    
    @staticmethod
    def get_cleaner_schedule(user_id: int) -> Dict[str, Any]:
        """
        Return upcoming confirmed or in_progress jobs for a cleaner.
        Ordered by date then start time.
        """
        today = date.today()
        jobs = (
            JobRequest.query
            .filter(
                JobRequest.cleaner_id == user_id,
                JobRequest.status.in_([JobStatus.confirmed, JobStatus.in_progress]),
                JobRequest.preferred_date >= today,
                JobRequest.deleted_at.is_(None),
            )
            .order_by(JobRequest.preferred_date.asc(), JobRequest.preferred_time_start.asc())
            .all()
        )
        return {"schedule": [j.to_dict() for j in jobs]}

    @staticmethod
    def get_available_jobs(user_id: int) -> Dict[str, Any]:
        """
        Return open (unassigned, pending) job requests that match the cleaner's
        service_type and fall within their availability slots.
        """
        cleaner_profile = CleanerProfile.query.filter_by(user_id=user_id).first()
        if not cleaner_profile:
            return {"job_requests": []}

        today = date.today()
        jobs = (
            JobRequest.query
            .filter(
                JobRequest.status == JobStatus.pending,
                JobRequest.service_type == cleaner_profile.service_type,
                JobRequest.preferred_date >= today,
                JobRequest.deleted_at.is_(None),
            )
            .order_by(JobRequest.preferred_date.asc(), JobRequest.preferred_time_start.asc())
            .all()
        )

        # If the cleaner has availability slots, only show jobs that fit within them.
        # If no slots are set, all matching jobs are shown.
        availability = cleaner_profile.availability
        if availability:
            jobs = [j for j in jobs if JobRequestService._job_fits_availability(j, availability)]

        return {"job_requests": [j.to_dict() for j in jobs]}

    @staticmethod
    def _job_fits_availability(job, slots) -> bool:
        """
        Return True if the job's preferred date/time falls within at least one
        availability slot.

        Date: job.preferred_date must be within [slot.start_date, slot.end_date].
        Time: only checked when the slot has a start_time set.
          - If the job has no preferred_time_start, it fits any timed slot.
          - Otherwise job.preferred_time_start must be >= slot.start_time, and
            if both slot and job have an end time, job end <= slot end.
        """
        for slot in slots:
            if not (slot.start_date <= job.preferred_date <= slot.end_date):
                continue

            # Date matches. Check time only if the slot has any time constraint.
            if slot.start_time is None and slot.end_time is None:
                return True  # slot covers the whole day

            # Job has no time preference at all — fits any open slot
            if job.preferred_time_start is None and job.preferred_time_end is None:
                return True

            # Check start time constraint (only if both slot and job have a start time)
            if slot.start_time is not None and job.preferred_time_start is not None:
                if job.preferred_time_start < slot.start_time:
                    continue  # job starts before cleaner is available

            # Check end time constraint (only if both slot and job have an end time)
            if slot.end_time is not None and job.preferred_time_end is not None:
                if job.preferred_time_end > slot.end_time:
                    continue  # job ends after cleaner is done

            return True

        return False

    # Helper for cleaner validation
    @staticmethod
    def _validate_cleaner_id(cleaner_id: int | None) -> int | None:
        if cleaner_id is None:
            return None

        cleaner = User.query.get(cleaner_id)
        if not cleaner:
            raise ValueError("not_found|Selected cleaner not found")

        if cleaner.role != UserRole.cleaner:
            raise ValueError("invalid_request|Selected user is not a cleaner")

        return cleaner_id
