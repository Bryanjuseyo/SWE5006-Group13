"""
Update job request status - route tests.
"""


def test_end_user_cancel_success(client, patch_decode_token, bearer_header, mocker):
    """End user can cancel a confirmed job request (cleaner assigned)."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_status",
        return_value={
            "message": "Job request status updated to cancelled.",
            "job_request": {"id": 1, "status": "cancelled"}
        }
    )

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={"status": "cancelled"}
    )
    assert res.status_code == 200
    body = res.get_json()
    assert "cancelled" in body["message"]


def test_end_user_cancel_no_cleaner_returns_403(client, patch_decode_token, bearer_header, mocker):
    """End user cannot cancel a job with no cleaner assigned."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_status",
        side_effect=ValueError(
            "forbidden|Cannot cancel a job request that has not been assigned to a cleaner."
        )
    )

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={"status": "cancelled"}
    )
    assert res.status_code == 403
    body = res.get_json()
    assert body["error"] == "forbidden"
    assert "not been assigned to a cleaner" in body["message"]


def test_cleaner_claim_unassigned_success(client, patch_decode_token, bearer_header, mocker):
    """Cleaner can accept an unassigned pending job."""
    patch_decode_token(payload={"user_id": 5, "email": "cleaner@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_status",
        return_value={
            "message": "Job request status updated to confirmed.",
            "job_request": {"id": 1, "status": "confirmed", "cleaner_id": 5}
        }
    )

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={"status": "confirmed"}
    )
    assert res.status_code == 200
    body = res.get_json()
    assert "confirmed" in body["message"]
    assert body["job_request"]["cleaner_id"] == 5


def test_cleaner_complete_success(client, patch_decode_token, bearer_header, mocker):
    """Cleaner can mark job as completed."""
    patch_decode_token(payload={"user_id": 5, "email": "cleaner@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_status",
        return_value={
            "message": "Job request status updated to completed.",
            "job_request": {"id": 1, "status": "completed"}
        }
    )

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={"status": "completed"}
    )
    assert res.status_code == 200


def test_missing_status_returns_400(client, patch_decode_token, bearer_header):
    """Status field is required for status update."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_request"
    assert "status is required" in body["message"]


def test_invalid_transition_returns_400(client, patch_decode_token, bearer_header, mocker):
    """US16: Invalid status transitions should fail."""
    patch_decode_token(payload={"user_id": 5, "email": "cleaner@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.update_job_status",
        side_effect=ValueError(
            "invalid_status|Cannot transition from confirmed to completed. Allowed: in_progress, cancelled."
        )
    )

    res = client.patch(
        "/api/job-requests/1/status",
        headers=bearer_header("valid"),
        json={"status": "completed"}
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_status"
