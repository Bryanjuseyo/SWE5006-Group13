"""
Unit tests for US-25: Cleaner Job Details View.

As a cleaner, I want to view full job request details before accepting a
booking, so that I can decide whether the job suits my skill, schedule,
and location.

Coverage focus:
  - Cleaner can view a job they are specifically assigned to (full details).
  - Cleaner can view an unassigned pending job (open listing, full details).
  - Cleaner can view a job whose priority window has expired (open to all).
  - Soft-deleted job returns not_found for cleaner.
  - Response contains all key booking detail fields.
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


CLEANER_ID = 5
OTHER_CLEANER_ID = 99

FULL_JOB_DICT = {
    "id": 1,
    "title": "Deep Clean 3-room HDB",
    "description": "Full deep clean including bathrooms and kitchen.",
    "service_type": "full",
    "location": "Blk 123 Ang Mo Kio Ave 4",
    "preferred_date": "2099-06-15",
    "preferred_time_start": "09:00:00",
    "preferred_time_end": "13:00:00",
    "status": "pending",
    "cleaner_id": None,
    "end_user_id": 1,
    "priority_window_end": None,
    "is_in_priority_window": False,
}


def _make_mock_job(mocker, *, cleaner_id=None, status=JobStatus.pending,
                   priority_window_end=None, deleted_at=None):
    mock_job = mocker.Mock()
    mock_job.cleaner_id = cleaner_id
    mock_job.status = status
    mock_job.priority_window_end = priority_window_end
    mock_job.deleted_at = deleted_at
    mock_job.to_dict.return_value = {**FULL_JOB_DICT, "cleaner_id": cleaner_id}
    return mock_job


def _patch_query(mocker, mock_job):
    q = mocker.Mock()
    q.options.return_value.filter_by.return_value.filter.return_value.first.return_value = mock_job
    mocker.patch("app.services.job_request_service.JobRequest.query", q)


# ---------------------------------------------------------------------------
# US-25 tests
# ---------------------------------------------------------------------------

def test_cleaner_can_view_job_assigned_to_them(mocker):
    """US-25: cleaner views full details of a job confirmed/assigned to them."""
    mock_job = _make_mock_job(mocker, cleaner_id=CLEANER_ID, status=JobStatus.confirmed)
    _patch_query(mocker, mock_job)

    result = JobRequestService.get_job_request(
        job_request_id=1, user_id=CLEANER_ID, role="cleaner"
    )

    assert result["job_request"]["id"] == 1
    assert result["job_request"]["cleaner_id"] == CLEANER_ID


def test_cleaner_job_details_response_contains_all_booking_fields(mocker):
    """US-25: the response for a cleaner-accessible job includes all key fields."""
    mock_job = _make_mock_job(mocker, cleaner_id=None, status=JobStatus.pending)
    _patch_query(mocker, mock_job)

    result = JobRequestService.get_job_request(
        job_request_id=1, user_id=CLEANER_ID, role="cleaner"
    )

    job = result["job_request"]
    for field in ("id", "title", "description", "service_type", "location",
                  "preferred_date", "preferred_time_start", "preferred_time_end", "status"):
        assert field in job, f"Missing field '{field}' in job details response"


def test_cleaner_can_view_job_after_priority_window_expires(mocker):
    """US-25: cleaner (not the preferred one) can view a job once its priority window has expired."""
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    mock_job = _make_mock_job(
        mocker,
        cleaner_id=OTHER_CLEANER_ID,   # preferred cleaner is someone else
        status=JobStatus.pending,
        priority_window_end=expired_time,
    )
    _patch_query(mocker, mock_job)

    # Should not raise — priority window has expired, job is open to all
    result = JobRequestService.get_job_request(
        job_request_id=1, user_id=CLEANER_ID, role="cleaner"
    )

    assert result["job_request"]["status"] == "pending"


def test_cleaner_cannot_view_soft_deleted_job(mocker):
    """US-25: a soft-deleted job returns not_found for a cleaner."""
    # Soft-deleted jobs are filtered out in the DB query (deleted_at IS NULL),
    # so the query returns None — simulated here by returning None from the mock.
    q = mocker.Mock()
    q.options.return_value.filter_by.return_value.filter.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.JobRequest.query", q)

    with pytest.raises(ValueError) as exc:
        JobRequestService.get_job_request(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner"
        )

    assert "not_found" in str(exc.value)


def test_cleaner_cannot_view_confirmed_job_assigned_to_different_cleaner(mocker):
    """US-25: cleaner cannot access a confirmed booking that belongs to another cleaner."""
    mock_job = _make_mock_job(
        mocker,
        cleaner_id=OTHER_CLEANER_ID,
        status=JobStatus.confirmed,
    )
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.get_job_request(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner"
        )

    assert "forbidden" in str(exc.value)
