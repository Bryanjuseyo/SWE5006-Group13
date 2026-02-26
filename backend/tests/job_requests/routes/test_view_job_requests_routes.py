"""
View job requests — route tests.
"""


def test_view_end_user_success(client, patch_decode_token, bearer_header, mocker):
    """End user can view their own job requests."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_requests",
        return_value={
            "job_requests": [
                {"id": 1, "title": "Job 1", "status": "pending"},
                {"id": 2, "title": "Job 2", "status": "completed"},
            ]
        }
    )

    res = client.get("/api/job-requests/", headers=bearer_header("valid"))
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["job_requests"]) == 2


def test_view_cleaner_sees_assigned_and_open(client, patch_decode_token, bearer_header, mocker):
    """Cleaner can view jobs assigned to them plus unassigned pending jobs."""
    patch_decode_token(payload={"user_id": 5, "email": "cleaner@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_requests",
        return_value={
            "job_requests": [
                {"id": 1, "title": "Open Job", "status": "pending", "cleaner_id": None},
                {"id": 2, "title": "My Job", "status": "confirmed", "cleaner_id": 5},
            ]
        }
    )

    res = client.get("/api/job-requests/", headers=bearer_header("valid"))
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["job_requests"]) == 2


def test_view_with_status_filter(client, patch_decode_token, bearer_header, mocker):
    """Can filter job requests by status."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    get_job_requests = mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_requests",
        return_value={"job_requests": []}
    )

    res = client.get("/api/job-requests/?status=pending", headers=bearer_header("valid"))
    assert res.status_code == 200

    get_job_requests.assert_called_once()
    call_args = get_job_requests.call_args[0]
    assert call_args[2] == "pending"  # status parameter passed through


def test_view_no_token_returns_401(client):
    """Listing job requests without token should return 401."""
    res = client.get("/api/job-requests/")
    assert res.status_code == 401


def test_view_by_id_success(client, patch_decode_token, bearer_header, mocker):
    """Can retrieve a single job request by ID."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_request",
        return_value={"job_request": {"id": 1, "title": "Test Job", "status": "pending"}}
    )

    res = client.get("/api/job-requests/1", headers=bearer_header("valid"))
    assert res.status_code == 200
    body = res.get_json()
    assert body["job_request"]["id"] == 1


def test_view_not_found_returns_404(client, patch_decode_token, bearer_header, mocker):
    """Returns 404 for non-existent job request."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_request",
        side_effect=ValueError("not_found|Job request not found.")
    )

    res = client.get("/api/job-requests/999", headers=bearer_header("valid"))
    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"


def test_view_forbidden_returns_403(client, patch_decode_token, bearer_header, mocker):
    """Returns 403 when user tries to view someone else's job request."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_job_request",
        side_effect=ValueError("forbidden|You are not authorized to view this job request.")
    )

    res = client.get("/api/job-requests/5", headers=bearer_header("valid"))
    assert res.status_code == 403
    body = res.get_json()
    assert body["error"] == "forbidden"
