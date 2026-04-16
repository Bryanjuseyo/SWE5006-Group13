"""
Update job request status - service layer tests.

"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus


def test_not_found_raises_error(mocker):
    """Updating status of non-existent job request should raise error."""
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = None
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=999, user_id=1, role="end_user", new_status="cancelled"
        )

    assert "not_found" in str(e.value)


def test_invalid_status_raises_error(mocker):
    """Invalid status value should raise error."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.status = JobStatus.pending

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="invalid_status"
        )

    assert "invalid_status" in str(e.value)


def test_end_user_cannot_set_non_cancel(mocker):
    """End user cannot change status to anything other than cancelled."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.confirmed

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="confirmed"
        )

    assert "forbidden" in str(e.value)
    assert "can only cancel" in str(e.value)


def test_end_user_cancel_no_cleaner_raises_error(mocker):
    """End user cannot cancel a job that has no cleaner assigned yet."""
    mock_job_request = mocker.Mock()
    mock_job_request.end_user_id = 1
    mock_job_request.cleaner_id = None
    mock_job_request.status = JobStatus.pending

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
        )

    assert "forbidden" in str(e.value)
    assert "not been assigned to a cleaner" in str(e.value)


def test_end_user_cancel_with_cleaner_success(mocker):
    """End user can cancel a confirmed job that has a cleaner assigned."""
    mock_job_request = mocker.Mock()
    mock_job_request.id = 1
    mock_job_request.end_user_id = 1
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.confirmed
    mock_job_request.to_dict.return_value = {"id": 1, "status": "cancelled"}
    mock_job_request.end_user = None
    mock_job_request.cleaner = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job_request,
    )
    mocker.patch("app.services.job_request_service.EmailService.send_booking_cancellation_email")

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=1, role="end_user", new_status="cancelled"
    )

    assert "cancelled" in result["message"]
    assert mock_job_request.status == JobStatus.cancelled


def test_cleaner_claim_unassigned_job_success(mocker):
    """Cleaner can claim an unassigned pending job"""
    mock_job_request = mocker.Mock()
    mock_job_request.id = 1
    mock_job_request.end_user_id = 2
    mock_job_request.cleaner_id = None  # unassigned
    mock_job_request.status = JobStatus.pending
    mock_job_request.to_dict.return_value = {"id": 1, "status": "confirmed", "cleaner_id": 5}
    mock_job_request.end_user = None
    mock_job_request.cleaner = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job_request,
    )
    mocker.patch("app.services.job_request_service.EmailService.send_booking_confirmation_email")

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=5, role="cleaner", new_status="confirmed"
    )

    assert "confirmed" in result["message"]
    assert mock_job_request.cleaner_id == 5
    assert mock_job_request.status == JobStatus.confirmed


def test_cleaner_cannot_accept_job_already_assigned_to_another_cleaner(mocker):
    """Cleaner cannot accept a job that is already assigned to another cleaner."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = 99
    mock_job_request.status = JobStatus.confirmed

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1,
            user_id=5,
            role="cleaner",
            new_status="confirmed"
        )

    assert "forbidden" in str(e.value)
    assert "not authorized" in str(e.value)


def test_cleaner_cannot_skip_to_completed_on_unassigned(mocker):
    """Cleaner can only confirm (not jump to other statuses) an unassigned job."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = None
    mock_job_request.status = JobStatus.pending

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=5, role="cleaner", new_status="completed"
        )

    assert "invalid_status" in str(e.value)


def test_cleaner_start_job_success(mocker):
    """Cleaner can move a confirmed job to in_progress."""
    mock_job_request = mocker.Mock()
    mock_job_request.id = 1
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.confirmed
    mock_job_request.to_dict.return_value = {"id": 1, "status": "in_progress"}

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job_request,
    )

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=5, role="cleaner", new_status="in_progress"
    )

    assert "in_progress" in result["message"]
    assert mock_job_request.status == JobStatus.in_progress


def test_cleaner_cancel_confirmed_job_success(mocker):
    """Cleaner can cancel a confirmed job that has not started yet."""
    mock_job_request = mocker.Mock()
    mock_job_request.id = 1
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.confirmed
    mock_job_request.to_dict.return_value = {"id": 1, "status": "cancelled"}
    mock_job_request.end_user = None
    mock_job_request.cleaner = None

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job_request,
    )
    mocker.patch("app.services.job_request_service.EmailService.send_booking_cancellation_email")

    result = JobRequestService.update_job_status(
        job_request_id=1,
        user_id=5,
        role="cleaner",
        new_status="cancelled"
    )

    assert "cancelled" in result["message"]
    assert mock_job_request.status == JobStatus.cancelled


def test_cleaner_cannot_cancel_in_progress_job(mocker):
    """Cleaner cannot cancel a job that has already started."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.in_progress

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1,
            user_id=5,
            role="cleaner",
            new_status="cancelled"
        )

    assert "invalid_status" in str(e.value)
    assert "Cannot transition" in str(e.value)


def test_cleaner_invalid_transition(mocker):
    """Cleaner cannot skip steps (confirmed → completed is not allowed)."""
    mock_job_request = mocker.Mock()
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.confirmed  # must go through in_progress first

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)

    with pytest.raises(ValueError) as e:
        JobRequestService.update_job_status(
            job_request_id=1, user_id=5, role="cleaner", new_status="completed"
        )

    assert "invalid_status" in str(e.value)
    assert "Cannot transition" in str(e.value)


def test_cleaner_complete_job_success(mocker):
    """Cleaner can mark an in_progress job as cleaner_completed."""
    mock_job_request = mocker.Mock()
    mock_job_request.id = 1
    mock_job_request.cleaner_id = 5
    mock_job_request.status = JobStatus.in_progress
    mock_job_request.to_dict.return_value = {"id": 1, "status": "cleaner_completed"}

    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job_request
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job_request,
    )

    result = JobRequestService.update_job_status(
        job_request_id=1, user_id=5, role="cleaner", new_status="cleaner_completed"
    )

    assert "completed" in result["message"]
    assert mock_job_request.status == JobStatus.cleaner_completed
