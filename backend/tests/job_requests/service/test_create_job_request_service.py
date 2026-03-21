"""
Create a new job request - service layer tests.
"""
import pytest
from datetime import date, datetime
from app.services.job_request_service import JobRequestService
from tests.job_requests.service.conftest import FUTURE_DATE, PAST_DATE, REQUIRED_FIELDS


def test_missing_title_raises_error(mocker):
    """Title is required when creating a job request."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={"description": "No title provided"}
        )

    assert "invalid_request" in str(e.value)
    assert "title is required" in str(e.value)


def test_missing_service_type_raises_error(mocker):
    """service_type is required when creating a job request."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={"title": "Test", "location": "123 Ang Mo Kio Street", "preferred_date": FUTURE_DATE}
        )

    assert "invalid_request" in str(e.value)
    assert "service_type is required" in str(e.value)


def test_missing_location_raises_error(mocker):
    """location is required when creating a job request."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={"title": "Test", "service_type": "full", "preferred_date": FUTURE_DATE}
        )

    assert "invalid_request" in str(e.value)
    assert "location is required" in str(e.value)


def test_missing_preferred_date_raises_error(mocker):
    """preferred_date is required when creating a job request."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={"title": "Test", "service_type": "full", "location": "123 Ang Mo Kio Street"}
        )

    assert "invalid_request" in str(e.value)
    assert "preferred_date is required" in str(e.value)


def test_invalid_service_type_raises_error(mocker):
    """Invalid service_type should raise error."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                "title": "Test",
                "service_type": "invalid_type",
                "location": "123 Ang Mo Kio Street",
                "preferred_date": FUTURE_DATE,
            }
        )

    assert "invalid_service_type" in str(e.value)


def test_past_date_raises_error(mocker):
    """preferred_date cannot be in the past."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                "title": "Test",
                "service_type": "full",
                "location": "123 Ang Mo Kio Street",
                "preferred_date": PAST_DATE,
            }
        )

    assert "invalid_date" in str(e.value)
    assert "cannot be in the past" in str(e.value)


def test_invalid_date_format_raises_error(mocker):
    """Invalid date format should raise error."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                "title": "Test",
                "service_type": "full",
                "location": "123 Ang Mo Kio Street",
                "preferred_date": "not-a-date",
            }
        )

    assert "invalid_date" in str(e.value)


def test_past_start_time_raises_error(mocker):
    """Start time cannot be in the past when the date is today."""
    mocker.patch("app.services.job_request_service.db.session")

    today = date.today()
    mock_dt = mocker.MagicMock()
    mock_dt.strptime = datetime.strptime
    mock_dt.now.return_value = datetime(today.year, today.month, today.day, 15, 0, 0)
    mocker.patch("app.services.job_request_service.datetime", mock_dt)

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                "title": "Test",
                "service_type": "full",
                "location": "123 Ang Mo Kio Street",
                "preferred_date": today.isoformat(),
                "preferred_time_start": "10:00",  # before mocked 15:00
            }
        )

    assert "invalid_time" in str(e.value)
    assert "cannot be in the past" in str(e.value)


def test_invalid_time_format_raises_error(mocker):
    """Invalid time format should raise error."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                **REQUIRED_FIELDS,
                "preferred_time_start": "not-a-time",
            }
        )

    assert "invalid_time" in str(e.value)


def test_end_time_before_start_raises_error(mocker):
    """End time must be strictly after start time."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                **REQUIRED_FIELDS,
                "preferred_time_start": "14:00",
                "preferred_time_end": "10:00",
            }
        )

    assert "invalid_time" in str(e.value)
    assert "strictly after" in str(e.value)


def test_equal_times_raises_error(mocker):
    """End time equal to start time is not allowed."""
    mocker.patch("app.services.job_request_service.db.session")

    with pytest.raises(ValueError) as e:
        JobRequestService.create_job_request(
            end_user_id=1,
            data={
                **REQUIRED_FIELDS,
                "preferred_time_start": "14:00",
                "preferred_time_end": "14:00",
            }
        )

    assert "invalid_time" in str(e.value)
    assert "strictly after" in str(e.value)


def test_create_success(mocker):
    """Successfully create a job request with all required fields."""
    mock_session = mocker.patch("app.services.job_request_service.db.session")

    mock_job_request = mocker.Mock()
    mock_job_request.to_dict.return_value = {
        "id": 1,
        "end_user_id": 1,
        "title": "House cleaning",
        "service_type": "full",
        "location": "123 Ang Mo Kio Street",
        "preferred_date": FUTURE_DATE,
        "status": "pending",
        "cleaner_id": 1
    }
    mocker.patch("app.services.job_request_service.JobRequest", return_value=mock_job_request)

    result = JobRequestService.create_job_request(
        end_user_id=1,
        data={**REQUIRED_FIELDS, "description": "Full cleaning"}
    )

    assert result["message"] == "Job request created successfully."
    assert result["job_request"]["title"] == "House cleaning"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
