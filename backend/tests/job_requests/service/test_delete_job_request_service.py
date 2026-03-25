"""
Delete a job request - service layer tests.
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


def test_not_found_raises_error(mocker):
    """Deleting non-existent job request should raise error."""
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.delete_job_request(job_request_id=999, user_id=1, role="end_user")

    assert "not_found" in str(e.value)


def test_not_owner_raises_error(mocker):
    """User cannot delete a job request they did not create."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 2
    mock_job_request.status = JobStatus.pending

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.delete_job_request(job_request_id=1, user_id=1, role="end_user")

    assert "forbidden" in str(e.value)


def test_in_progress_raises_error(mocker):
    """Cannot delete a job request that is in progress."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.in_progress

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.delete_job_request(job_request_id=1, user_id=1, role="end_user")

    assert "invalid_status" in str(e.value)


def test_delete_success(mocker):
    """Successfully soft-delete a job request (sets deleted_at, does not remove the record)."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending
    mock_job_request.deleted_at = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mock_session = mocker.patch("app.services.job_request_service.db.session")

    result = JobRequestService.delete_job_request(job_request_id=1, user_id=1, role="end_user")

    assert result["message"] == "Job request deleted successfully."
    assert mock_job_request.deleted_at is not None
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_called_once()
