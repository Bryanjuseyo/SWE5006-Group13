"""
Update job request details - route tests.
"""
from tests.job_requests.routes.conftest import PAST_DATE


def test_update_success(client, patch_decode_token, bearer_header, mocker):
    """End user can update their job request."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_request",
        return_value={
            "message": "Job request updated successfully.",
            "job_request": {"id": 1, "title": "Updated Title"}
        }
    )

    res = client.put(
        "/api/job-requests/1",
        headers=bearer_header("valid"),
        json={"title": "Updated Title"}
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Job request updated successfully."
    assert body["job_request"]["title"] == "Updated Title"


def test_past_date_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Cannot update preferred_date to a past date."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_request",
        side_effect=ValueError("invalid_date|preferred_date cannot be in the past.")
    )

    res = client.put(
        "/api/job-requests/1",
        headers=bearer_header("valid"),
        json={"preferred_date": PAST_DATE}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_date"
    assert "cannot be in the past" in body["message"]


def test_not_owner_returns_403(client, patch_decode_token, bearer_header, mocker):
    """Cannot update job request created by another user."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_request",
        side_effect=ValueError("forbidden|You are not authorized to update this job request.")
    )

    res = client.put(
        "/api/job-requests/5",
        headers=bearer_header("valid"),
        json={"title": "Hacked Title"}
    )
    assert res.status_code == 403


def test_cleaner_role_returns_403(client, patch_decode_token, bearer_header):
    """Cleaners cannot update job requests (only end_user role allowed)."""
    patch_decode_token(payload={"user_id": 5, "email": "cleaner@test.com", "role": "cleaner"})

    res = client.put(
        "/api/job-requests/1",
        headers=bearer_header("valid"),
        json={"title": "Updated"}
    )
    assert res.status_code == 403
