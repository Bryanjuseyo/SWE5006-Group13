"""
Delete a job request - route tests.
"""


def test_delete_success(client, patch_decode_token, bearer_header, mocker):
    """End user can delete their job request."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.delete_job_request",
        return_value={"message": "Job request deleted successfully."}
    )

    res = client.delete("/api/job-requests/1", headers=bearer_header("valid"))
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Job request deleted successfully."


def test_not_found_returns_404(client, patch_decode_token, bearer_header, mocker):
    """Returns 404 when deleting non-existent job request."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.delete_job_request",
        side_effect=ValueError("not_found|Job request not found.")
    )

    res = client.delete("/api/job-requests/999", headers=bearer_header("valid"))
    assert res.status_code == 404


def test_in_progress_returns_400(client, patch_decode_token, bearer_header, mocker):
    """Cannot delete job request that is in progress."""
    patch_decode_token(payload={"user_id": 1, "email": "user@test.com", "role": "end_user"})

    mocker.patch(
        "app.services.job_request_service.JobRequestService.delete_job_request",
        side_effect=ValueError(
            "invalid_status|Cannot delete a job request that is in progress or completed."
        )
    )

    res = client.delete("/api/job-requests/1", headers=bearer_header("valid"))
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_status"
