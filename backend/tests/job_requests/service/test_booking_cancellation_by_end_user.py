"""
Unit tests for US-30: Booking Cancellation by End-User.

As an end-user, I want to cancel an upcoming booking before it starts,
so that I can handle changes in my plans.

Rules enforced by the service:
  - Only the job owner (end_user_id == user_id) may cancel.
  - A cleaner must already be assigned (cleaner_id is not None).
  - Status must be pending or confirmed (not in_progress / completed).
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


def _make_mock_job(mocker, *, end_user_id=1, cleaner_id=5, status=JobStatus.confirmed):
    mock_job = mocker.Mock()
    mock_job.end_user_id = end_user_id
    mock_job.cleaner_id = cleaner_id
    mock_job.status = status
    mock_job.to_dict.return_value = {"id": 1, "status": "cancelled"}
    # Minimal relationship mocks so the email block doesn't error
    mock_job.end_user = mocker.Mock(id=end_user_id, email="user@test.com")
    mock_job.cleaner = mocker.Mock(id=cleaner_id, email="cleaner@test.com")
    return mock_job


def _patch_query(mocker, mock_job):
    q = mocker.Mock()
    q.filter_by.return_value.filter.return_value.first.return_value = mock_job
    mocker.patch("app.services.job_request_service.JobRequest.query", q)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch("app.services.job_request_service.UserProfile.query").filter_by.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.EmailService.send_booking_cancellation_email")


# ---------------------------------------------------------------------------
# US-30 tests
# ---------------------------------------------------------------------------

def test_end_user_can_cancel_confirmed_job_with_cleaner(mocker):
    """US-30 (happy path): end_user cancels a confirmed, cleaner-assigned job."""
    mock_job = _make_mock_job(mocker, status=JobStatus.confirmed)
    _patch_query(mocker, mock_job)

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
    )

    assert mock_job.status == JobStatus.cancelled
    assert "cancelled" in result["message"]


def test_end_user_can_cancel_pending_job_with_cleaner_assigned(mocker):
    """US-30: end_user can also cancel a pending job if a cleaner is already assigned."""
    mock_job = _make_mock_job(mocker, status=JobStatus.pending, cleaner_id=5)
    _patch_query(mocker, mock_job)

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
    )

    assert mock_job.status == JobStatus.cancelled
    assert "cancelled" in result["message"]


def test_end_user_cannot_cancel_job_without_cleaner_assigned(mocker):
    """US-30: cancellation rejected when no cleaner has accepted the booking."""
    mock_job = _make_mock_job(mocker, cleaner_id=None, status=JobStatus.pending)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
        )

    assert "forbidden" in str(exc.value)
    assert "not been assigned" in str(exc.value)


def test_end_user_cannot_cancel_job_in_progress(mocker):
    """US-30: cancellation rejected when the job has already started."""
    mock_job = _make_mock_job(mocker, status=JobStatus.in_progress)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
        )

    assert "invalid_status" in str(exc.value)
    assert "pending or confirmed" in str(exc.value)


def test_end_user_cannot_cancel_another_users_job(mocker):
    """US-30: cancellation rejected when the requester is not the job owner."""
    mock_job = _make_mock_job(mocker, end_user_id=99, status=JobStatus.confirmed)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
        )

    assert "forbidden" in str(exc.value)
    assert "not authorized" in str(exc.value)
