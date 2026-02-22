"""
View job requests — service layer tests.
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


def test_view_not_found_raises_error(mocker):
    """Viewing non-existent job request should raise error."""
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.get_job_request(job_request_id=999, user_id=1, role="end_user")

    assert "not_found" in str(e.value)


def test_end_user_view_other_user_request_raises_error(mocker):
    """End user cannot view a job request they did not create."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 2
    mock_job_request.cleaner_id = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.get_job_request(job_request_id=1, user_id=1, role="end_user")

    assert "forbidden" in str(e.value)


def test_cleaner_can_view_unassigned_pending(mocker):
    """Cleaner can view an unassigned pending job."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = None
    mock_job_request.status = JobStatus.pending
    mock_job_request.to_dict.return_value = {"id": 1, "status": "pending", "cleaner_id": None}

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    result = JobRequestService.get_job_request(job_request_id=1, user_id=5, role="cleaner")

    assert result["job_request"]["id"] == 1


def test_cleaner_forbidden_for_other_cleaners_job_request(mocker):
    """Cleaner cannot view a job assigned to a different cleaner."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = 99  # assigned to someone else
    mock_job_request.status = JobStatus.confirmed

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.get_job_request(job_request_id=1, user_id=5, role="cleaner")

    assert "forbidden" in str(e.value)


def test_get_success(mocker):
    """Successfully view a job request."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.to_dict.return_value = {"id": 1, "title": "Test"}

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    result = JobRequestService.get_job_request(job_request_id=1, user_id=1, role="end_user")

    assert result["job_request"]["id"] == 1
