"""
Create a new job request - route tests.
"""
from tests.job_requests.routes.conftest import FUTURE_DATE, PAST_DATE, VALID_PAYLOAD


def test_create_success(client, patch_decode_token, bearer_header, mocker):
    """End user can successfully create a job request"""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        return_value={
            "message": "Job request created successfully.",
            "job_request": {
                "id": 1,
                "end_user_id": 1,
                "title": "House cleaning",
                "service_type": "full",
                "location": "123 Ang Mo Kio Street",
                "preferred_date": FUTURE_DATE,
                "status": "pending",
            }
        }
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json=VALID_PAYLOAD
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["message"] == "Job request created successfully."
    assert body["job_request"]["title"] == "House cleaning"


def test_missing_title_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Creating job request without title should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_request|title is required.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={"description": "No title provided"}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_request"
    assert "title is required" in body["message"]


def test_missing_service_type_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Creating job request without service_type should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_request|service_type is required.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={"title": "Test", "location": "123 Ang Mo Kio Street", "preferred_date": FUTURE_DATE}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_request"
    assert "service_type is required" in body["message"]


def test_missing_location_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Creating job request without location should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_request|location is required.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={"title": "Test", "service_type": "full", "preferred_date": FUTURE_DATE}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_request"
    assert "location is required" in body["message"]


def test_missing_preferred_date_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Creating job request without preferred_date should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_request|preferred_date is required.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={"title": "Test", "service_type": "full", "location": "123 Ang Mo Kio Street"}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_request"
    assert "preferred_date is required" in body["message"]


def test_past_date_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Creating job request with a past date should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_date|preferred_date cannot be in the past.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={**VALID_PAYLOAD, "preferred_date": PAST_DATE}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_date"
    assert "cannot be in the past" in body["message"]


def test_past_start_time_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Start time in the past (for today's date) should fail."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError("invalid_time|preferred_time_start cannot be in the past.")
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={**VALID_PAYLOAD, "preferred_time_start": "00:01"}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_time"


def test_end_time_not_after_start_returns_400(client, patch_decode_token, bearer_header, mocker):
    """End time must be strictly after start time."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.create_job_request",
        side_effect=ValueError(
            "invalid_time|preferred_time_end must be strictly after preferred_time_start."
        )
    )

    res = client.post(
        "/api/job-requests/",
        headers=bearer_header("valid"),
        json={**VALID_PAYLOAD, "preferred_time_start": "14:00", "preferred_time_end": "14:00"}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_time"
    assert "strictly after" in body["message"]


def test_no_token_returns_401(client):
    """Creating job request without token should return 401."""
    res = client.post("/api/job-requests/", json={"title": "Test"})
    assert res.status_code == 401
