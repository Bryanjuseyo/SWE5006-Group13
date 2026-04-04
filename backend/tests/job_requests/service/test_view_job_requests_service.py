"""
View job requests - service layer tests.
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus, ServiceType
from datetime import datetime, timezone, timedelta


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
    mock_job_request.priority_window_end = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_job_request.deleted_at = None
    mock_job_request.to_dict.return_value = {
        "id": 1,
        "status": "pending",
        "cleaner_id": None,
    }

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


# get_job_requests tests
def test_cleaner_get_job_requests_only_matching_service_type(mocker):
    """Cleaner should only receive open pending jobs matching their service type."""
    # cleaner profile = partial
    mock_profile = mocker.Mock()
    mock_profile.service_type = ServiceType.partial

    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    # returned jobs should only be the matching ones
    mock_job_1 = mocker.Mock()
    mock_job_1.to_dict.return_value = {"id": 1, "service_type": "partial"}

    mock_job_2 = mocker.Mock()
    mock_job_2.to_dict.return_value = {"id": 2, "service_type": "partial"}

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_job_1, mock_job_2
    ]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_job_requests(user_id=5, role="cleaner")

    assert len(result["job_requests"]) == 2
    assert result["job_requests"][0]["service_type"] == "partial"
    assert result["job_requests"][1]["service_type"] == "partial"
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


def test_cleaner_get_job_requests_no_profile_only_assigned_jobs(mocker):
    """Cleaner with no profile should only receive assigned jobs, not open jobs."""
    # no cleaner profile
    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    # only assigned job returned from query
    mock_assigned_job = mocker.Mock()
    mock_assigned_job.to_dict.return_value = {
        "id": 10,
        "cleaner_id": 5,
        "status": "confirmed"
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_assigned_job
    ]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_job_requests(user_id=5, role="cleaner")

    assert len(result["job_requests"]) == 1
    assert result["job_requests"][0]["cleaner_id"] == 5
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


# get_available_jobs tests
def test_get_available_jobs_only_matching_service_type(mocker):
    """Available jobs should only include pending jobs matching cleaner service type."""
    mock_profile = mocker.Mock()
    mock_profile.service_type = ServiceType.full
    mock_profile.availability = []

    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    mock_job_1 = mocker.Mock()
    mock_job_1.to_dict.return_value = {"id": 21, "service_type": "full", "status": "pending"}

    mock_job_2 = mocker.Mock()
    mock_job_2.to_dict.return_value = {"id": 22, "service_type": "full", "status": "pending"}

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [
        mock_job_1, mock_job_2
    ]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_available_jobs(user_id=5)

    assert len(result["job_requests"]) == 2
    assert result["job_requests"][0]["service_type"] == "full"
    assert result["job_requests"][1]["service_type"] == "full"
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


def test_get_available_jobs_no_cleaner_profile_returns_empty(mocker):
    """If cleaner has no profile, available jobs should be empty."""
    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    result = JobRequestService.get_available_jobs(user_id=5)

    assert result == {"job_requests": []}
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


def test_get_available_jobs_returns_jobs_within_availability(mocker):
    """Available jobs should include jobs that fit within cleaner availability slots."""
    mock_profile = mocker.Mock()
    mock_profile.service_type = ServiceType.full

    slot = mocker.Mock()
    slot.start_date = __import__("datetime").date(2026, 3, 20)
    slot.end_date = __import__("datetime").date(2026, 3, 20)
    slot.start_time = __import__("datetime").time(9, 0)
    slot.end_time = __import__("datetime").time(12, 0)
    mock_profile.availability = [slot]

    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    matching_job = mocker.Mock()
    matching_job.preferred_date = __import__("datetime").date(2026, 3, 20)
    matching_job.preferred_time_start = __import__("datetime").time(10, 0)
    matching_job.preferred_time_end = __import__("datetime").time(11, 0)
    matching_job.to_dict.return_value = {
        "id": 31,
        "service_type": "full",
        "status": "pending",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "10:00",
        "preferred_time_end": "11:00",
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [matching_job]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_available_jobs(user_id=5)

    assert len(result["job_requests"]) == 1
    assert result["job_requests"][0]["id"] == 31
    assert result["job_requests"][0]["preferred_time_start"] == "10:00"
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


def test_get_available_jobs_excludes_jobs_outside_availability(mocker):
    """Available jobs should exclude jobs outside cleaner availability slots."""
    mock_profile = mocker.Mock()
    mock_profile.service_type = ServiceType.full

    slot = mocker.Mock()
    slot.start_date = __import__("datetime").date(2026, 3, 20)
    slot.end_date = __import__("datetime").date(2026, 3, 20)
    slot.start_time = __import__("datetime").time(9, 0)
    slot.end_time = __import__("datetime").time(12, 0)
    mock_profile.availability = [slot]

    mock_cleaner_profile_query = mocker.Mock()
    mock_cleaner_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.job_request_service.CleanerProfile.query", mock_cleaner_profile_query)

    outside_job = mocker.Mock()
    outside_job.preferred_date = __import__("datetime").date(2026, 3, 20)
    outside_job.preferred_time_start = __import__("datetime").time(13, 0)
    outside_job.preferred_time_end = __import__("datetime").time(14, 0)
    outside_job.to_dict.return_value = {
        "id": 32,
        "service_type": "full",
        "status": "pending",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "13:00",
        "preferred_time_end": "14:00",
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [outside_job]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_available_jobs(user_id=5)

    assert result["job_requests"] == []
    mock_cleaner_profile_query.filter_by.assert_called_once_with(user_id=5)


def test_get_cleaner_schedule_returns_upcoming_confirmed_and_in_progress_jobs(mocker):
    """Cleaner schedule should return upcoming confirmed and in-progress jobs."""
    job_1 = mocker.Mock()
    job_1.to_dict.return_value = {
        "id": 41,
        "cleaner_id": 5,
        "status": "confirmed",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "09:00",
    }

    job_2 = mocker.Mock()
    job_2.to_dict.return_value = {
        "id": 42,
        "cleaner_id": 5,
        "status": "in_progress",
        "preferred_date": "2026-03-21",
        "preferred_time_start": "10:00",
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [job_1, job_2]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_cleaner_schedule(user_id=5)

    assert len(result["schedule"]) == 2
    assert result["schedule"][0]["status"] == "confirmed"
    assert result["schedule"][1]["status"] == "in_progress"


def test_get_cleaner_schedule_excludes_past_jobs(mocker):
    """Cleaner schedule should exclude past jobs and only return upcoming ones."""
    upcoming_job = mocker.Mock()
    upcoming_job.to_dict.return_value = {
        "id": 43,
        "cleaner_id": 5,
        "status": "confirmed",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "11:00",
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [upcoming_job]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_cleaner_schedule(user_id=5)

    assert len(result["schedule"]) == 1
    assert result["schedule"][0]["id"] == 43


def test_get_cleaner_schedule_returns_empty_when_no_jobs(mocker):
    """Cleaner schedule should be empty when there are no upcoming jobs."""
    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = []
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_cleaner_schedule(user_id=5)

    assert result == {"schedule": []}


def test_get_cleaner_schedule_orders_by_date_then_start_time(mocker):
    """Cleaner schedule should preserve ordering by preferred date then start time."""
    earlier_time_job = mocker.Mock()
    earlier_time_job.to_dict.return_value = {
        "id": 44,
        "cleaner_id": 5,
        "status": "confirmed",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "09:00",
    }

    later_time_job = mocker.Mock()
    later_time_job.to_dict.return_value = {
        "id": 45,
        "cleaner_id": 5,
        "status": "confirmed",
        "preferred_date": "2026-03-20",
        "preferred_time_start": "14:00",
    }

    next_day_job = mocker.Mock()
    next_day_job.to_dict.return_value = {
        "id": 46,
        "cleaner_id": 5,
        "status": "in_progress",
        "preferred_date": "2026-03-21",
        "preferred_time_start": "08:00",
    }

    mock_job_query = mocker.Mock()
    mock_job_query.filter.return_value.order_by.return_value.all.return_value = [
        earlier_time_job,
        later_time_job,
        next_day_job,
    ]
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_job_query)

    result = JobRequestService.get_cleaner_schedule(user_id=5)

    assert [job["id"] for job in result["schedule"]] == [44, 45, 46]
