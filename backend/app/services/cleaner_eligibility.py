from typing import Iterable

from sqlalchemy import and_, or_

from app.models import JobRequest, JobStatus


def schedule_fits_availability(
    preferred_date,
    preferred_time_start,
    preferred_time_end,
    slots: Iterable,
    *,
    require_slot: bool = False,
) -> bool:
    slots = list(slots or [])
    if not slots:
        return not require_slot

    for slot in slots:
        if not (slot.start_date <= preferred_date <= slot.end_date):
            continue

        if slot.start_time is None and slot.end_time is None:
            return True

        if preferred_time_start is None and preferred_time_end is None:
            return True

        if slot.start_time is not None and preferred_time_start is not None:
            if preferred_time_start < slot.start_time:
                continue

        if slot.end_time is not None and preferred_time_end is not None:
            if preferred_time_end > slot.end_time:
                continue

        return True

    return False


def has_booking_conflict(
    cleaner_id: int,
    preferred_date,
    preferred_time_start=None,
    preferred_time_end=None,
    *,
    exclude_job_request_id: int | None = None,
) -> bool:
    filters = [
        JobRequest.cleaner_id == cleaner_id,
        JobRequest.deleted_at.is_(None),
        JobRequest.status.in_([JobStatus.confirmed, JobStatus.in_progress]),
        JobRequest.preferred_date == preferred_date,
    ]

    if exclude_job_request_id is not None:
        filters.append(JobRequest.id != exclude_job_request_id)

    if preferred_time_start is not None and preferred_time_end is not None:
        filters.append(
            or_(
                JobRequest.preferred_time_start.is_(None),
                JobRequest.preferred_time_end.is_(None),
                and_(
                    JobRequest.preferred_time_start < preferred_time_end,
                    JobRequest.preferred_time_end > preferred_time_start,
                ),
            )
        )

    return JobRequest.query.filter(*filters).first() is not None
