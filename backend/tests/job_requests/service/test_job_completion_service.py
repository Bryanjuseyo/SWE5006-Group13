"""
Unit tests for:
  US-31: Cleaner Mark Job as Complete
    As a cleaner, I want to mark a job as complete after finishing the service.

  US-32: End-user Completion Acknowledgement
    As an end-user, I want to confirm that a cleaning job has been completed,
    so that the system can close the booking accurately.

Status flow:
  in_progress  --[cleaner]--> cleaner_completed   (US-31)
  cleaner_completed --[end_user]--> completed      (US-32)
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


def _make_mock_job(mocker, *, end_user_id=1, cleaner_id=5, status):
    mock_job = mocker.Mock()
    mock_job.end_user_id = end_user_id
    mock_job.cleaner_id = cleaner_id
    mock_job.status = status
    mock_job.to_dict.return_value = {"id": 1, "status": status.value}
    mock_job.end_user = mocker.Mock(id=end_user_id, email="user@test.com")
    mock_job.cleaner = mocker.Mock(id=cleaner_id, email="cleaner@test.com")
    return mock_job


def _patch_query(mocker, mock_job):
    q = mocker.Mock()
    q.filter_by.return_value.filter.return_value.first.return_value = mock_job
    mocker.patch("app.services.job_request_service.JobRequest.query", q)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch("app.services.job_request_service.UserProfile.query").filter_by.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.EmailService.send_booking_confirmation_email")
    mocker.patch("app.services.job_request_service.EmailService.send_booking_cancellation_email")


# ===========================================================================
# US-31: Cleaner marks job as cleaner_completed
# ===========================================================================

def test_cleaner_can_mark_in_progress_job_as_completed(mocker):
    """US-31 (happy path): cleaner transitions in_progress → cleaner_completed."""
    mock_job = _make_mock_job(mocker, cleaner_id=5, status=JobStatus.in_progress)
    mock_job.to_dict.return_value = {"id": 1, "status": "cleaner_completed"}
    _patch_query(mocker, mock_job)

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=5, role="cleaner", new_status="cleaner_completed"
    )

    assert mock_job.status == JobStatus.cleaner_completed
    assert "cleaner_completed" in result["message"]


def test_cleaner_cannot_skip_directly_to_cleaner_completed_from_confirmed(mocker):
    """US-31: cleaner must start the job before marking complete (confirmed → cleaner_completed invalid)."""
    mock_job = _make_mock_job(mocker, cleaner_id=5, status=JobStatus.confirmed)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=5, role="cleaner", new_status="cleaner_completed"
        )

    assert "invalid_status" in str(exc.value)
    assert "Cannot transition" in str(exc.value)


def test_unassigned_cleaner_cannot_mark_job_complete(mocker):
    """US-31: a cleaner who is not assigned to the job cannot mark it complete."""
    mock_job = _make_mock_job(mocker, cleaner_id=99, status=JobStatus.in_progress)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=5, role="cleaner", new_status="cleaner_completed"
        )

    assert "forbidden" in str(exc.value)
    assert "not authorized" in str(exc.value)


def test_cleaner_cannot_mark_already_completed_job(mocker):
    """US-31: cleaner cannot re-mark a job that is already cleaner_completed."""
    mock_job = _make_mock_job(mocker, cleaner_id=5, status=JobStatus.cleaner_completed)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=5, role="cleaner", new_status="cleaner_completed"
        )

    assert "invalid_status" in str(exc.value)


# ===========================================================================
# US-32: End-user acknowledges job completion
# ===========================================================================

def test_end_user_can_confirm_completion_after_cleaner_marks_done(mocker):
    """US-32 (happy path): end_user transitions cleaner_completed → completed."""
    mock_job = _make_mock_job(mocker, end_user_id=1, cleaner_id=5, status=JobStatus.cleaner_completed)
    mock_job.to_dict.return_value = {"id": 1, "status": "completed"}
    _patch_query(mocker, mock_job)

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=1, role="end_user", new_status="completed"
    )

    assert mock_job.status == JobStatus.completed
    assert "completed" in result["message"]


def test_end_user_cannot_confirm_completion_if_still_in_progress(mocker):
    """US-32: end_user cannot mark as completed while job is still in_progress."""
    mock_job = _make_mock_job(mocker, end_user_id=1, cleaner_id=5, status=JobStatus.in_progress)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="completed"
        )

    assert "invalid_status" in str(exc.value)
    assert "cleaner has marked" in str(exc.value)


def test_end_user_cannot_confirm_completion_from_confirmed_status(mocker):
    """US-32: end_user cannot skip the cleaner_completed step."""
    mock_job = _make_mock_job(mocker, end_user_id=1, cleaner_id=5, status=JobStatus.confirmed)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="completed"
        )

    assert "invalid_status" in str(exc.value)


def test_end_user_cannot_confirm_completion_for_another_users_job(mocker):
    """US-32: end_user cannot acknowledge completion on a job they don't own."""
    mock_job = _make_mock_job(mocker, end_user_id=99, cleaner_id=5, status=JobStatus.cleaner_completed)
    _patch_query(mocker, mock_job)

    with pytest.raises(ValueError) as exc:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="completed"
        )

    assert "forbidden" in str(exc.value)
    assert "not authorized" in str(exc.value)
