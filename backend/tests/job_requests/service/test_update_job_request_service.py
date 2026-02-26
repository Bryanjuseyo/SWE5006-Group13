"""
Update job request details — service layer tests.
"""
import pytest
from datetime import date, datetime
from app.services.job_request_service import JobRequestService
from app.models import JobStatus
from tests.job_requests.service.conftest import FUTURE_DATE, PAST_DATE


def test_not_found_raises_error(mocker):
    """Updating non-existent job request should raise error."""
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=999, user_id=1, role="end_user", data={"title": "Updated"}
        )

    assert "not_found" in str(e.value)


def test_not_owner_raises_error(mocker):
    """User cannot update a job request they did not create."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 2  # different user

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=1, user_id=1, role="end_user", data={"title": "Updated"}
        )

    assert "forbidden" in str(e.value)


def test_completed_raises_error(mocker):
    """Cannot update a completed job request."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.completed

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=1, user_id=1, role="end_user", data={"title": "Updated"}
        )

    assert "invalid_status" in str(e.value)


def test_past_date_raises_error(mocker):
    """preferred_date cannot be updated to a past date."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending
    mock_job_request.preferred_time_start = None
    mock_job_request.preferred_time_end = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=1,
            user_id=1,
            role="end_user",
            data={"preferred_date": PAST_DATE}
        )

    assert "invalid_date" in str(e.value)
    assert "cannot be in the past" in str(e.value)


def test_past_start_time_raises_error(mocker):
    """Start time cannot be updated to a past time when the date is today."""
    today = date.today()

    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending
    mock_job_request.preferred_date = today
    mock_job_request.preferred_time_start = None
    mock_job_request.preferred_time_end = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    mock_dt = mocker.MagicMock()
    mock_dt.strptime = datetime.strptime
    mock_dt.now.return_value = datetime(today.year, today.month, today.day, 15, 0, 0)
    mocker.patch("app.services.job_request_service.datetime", mock_dt)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=1,
            user_id=1,
            role="end_user",
            data={"preferred_time_start": "10:00"}  # before mocked 15:00
        )

    assert "invalid_time" in str(e.value)
    assert "cannot be in the past" in str(e.value)


def test_equal_times_raises_error(mocker):
    """End time equal to start time should be rejected."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending
    mock_job_request.preferred_time_start = None
    mock_job_request.preferred_time_end = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_request(
            job_request_id=1,
            user_id=1,
            role="end_user",
            data={
                "preferred_date": FUTURE_DATE,
                "preferred_time_start": "10:00",
                "preferred_time_end": "10:00",
            }
        )

    assert "invalid_time" in str(e.value)
    assert "strictly after" in str(e.value)


def test_update_success(mocker):
    """Successfully update a job request."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending
    mock_job_request.preferred_time_start = None
    mock_job_request.preferred_time_end = None
    mock_job_request.to_dict.return_value = {"id": 1, "title": "Updated"}

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")

    result = JobRequestService.update_job_request(
        job_request_id=1, user_id=1, role="end_user", data={"title": "Updated"}
    )

    assert result["message"] == "Job request updated successfully."
