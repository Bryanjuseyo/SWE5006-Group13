import pytest
from jwt import ExpiredSignatureError


# ---------------------------------------------------------------------------
# GET /api/cleaner/availability
# ---------------------------------------------------------------------------

def test_get_availability_returns_200(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.get_availability",
        return_value=[{"id": 1, "start_date": "2099-01-01"}],
    )

    res = client.get("/api/cleaner/availability", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert res.get_json() == [{"id": 1, "start_date": "2099-01-01"}]


def test_get_availability_missing_token_returns_401(client):
    res = client.get("/api/cleaner/availability")
    assert res.status_code == 401
    assert res.get_json()["error"] == "unauthorized"


def test_get_availability_expired_token_returns_401(client, patch_decode_token, bearer_header):
    patch_decode_token(exc=ExpiredSignatureError())
    res = client.get("/api/cleaner/availability", headers=bearer_header("expired"))
    assert res.status_code == 401
    assert res.get_json()["error"] == "unauthorized"


# ---------------------------------------------------------------------------
# POST /api/cleaner/availability
# ---------------------------------------------------------------------------

def test_post_availability_returns_201_on_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.add_availability",
        return_value={"message": "Availability slot added.", "availability": {"id": 2}},
    )

    res = client.post(
        "/api/cleaner/availability",
        headers=bearer_header("ok"),
        json={"start_date": "2099-01-01", "end_date": "2099-01-01"},
    )
    assert res.status_code == 201
    assert res.get_json()["message"] == "Availability slot added."


def test_post_availability_returns_400_on_value_error(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.add_availability",
        side_effect=ValueError("invalid_date|end_date must be on or after start_date"),
    )

    res = client.post(
        "/api/cleaner/availability",
        headers=bearer_header("ok"),
        json={"start_date": "2099-01-02", "end_date": "2099-01-01"},
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_date"


# ---------------------------------------------------------------------------
# PUT /api/cleaner/availability/<id>
# ---------------------------------------------------------------------------

def test_put_availability_returns_200_on_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.update_availability",
        return_value={"message": "Availability slot updated.", "availability": {"id": 3}},
    )

    res = client.put(
        "/api/cleaner/availability/3",
        headers=bearer_header("ok"),
        json={"start_time": "10:00", "end_time": "12:00"},
    )
    assert res.status_code == 200
    assert res.get_json()["message"] == "Availability slot updated."


def test_put_availability_returns_400_on_not_found_value_error(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.update_availability",
        side_effect=ValueError("not_found|Availability slot not found."),
    )

    res = client.put(
        "/api/cleaner/availability/999",
        headers=bearer_header("ok"),
        json={},
    )
    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"


# ---------------------------------------------------------------------------
# DELETE /api/cleaner/availability/<id>
# ---------------------------------------------------------------------------

def test_delete_availability_returns_200_on_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.delete_availability",
        return_value={"message": "Availability slot removed."},
    )

    res = client.delete("/api/cleaner/availability/1", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert res.get_json()["message"] == "Availability slot removed."


def test_delete_availability_returns_404_on_not_found(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.delete_availability",
        side_effect=ValueError("not_found|Availability slot not found."),
    )

    res = client.delete("/api/cleaner/availability/999", headers=bearer_header("ok"))
    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"


# ---------------------------------------------------------------------------
# GET /api/cleaner/schedule
# ---------------------------------------------------------------------------

def test_get_schedule_returns_200(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_cleaner_schedule",
        return_value={"items": [], "total": 0, "page": 1, "per_page": 25},
    )

    res = client.get("/api/cleaner/schedule", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert "items" in res.get_json()


def test_get_schedule_with_pagination_params(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mock_svc = mocker.patch(
        "app.services.job_request_service.JobRequestService.get_cleaner_schedule",
        return_value={"items": [], "total": 0, "page": 2, "per_page": 10},
    )

    res = client.get("/api/cleaner/schedule?page=2&per_page=10", headers=bearer_header("ok"))
    assert res.status_code == 200
    mock_svc.assert_called_once_with(7, 2, 10)


# ---------------------------------------------------------------------------
# GET /api/cleaner/available-jobs
# ---------------------------------------------------------------------------

def test_get_available_jobs_returns_200(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mocker.patch(
        "app.services.job_request_service.JobRequestService.get_available_jobs",
        return_value={"items": [], "total": 0, "page": 1, "per_page": 25},
    )

    res = client.get("/api/cleaner/available-jobs", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert "items" in res.get_json()


def test_get_available_jobs_with_pagination_params(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    mock_svc = mocker.patch(
        "app.services.job_request_service.JobRequestService.get_available_jobs",
        return_value={"items": [], "total": 0, "page": 3, "per_page": 5},
    )

    res = client.get("/api/cleaner/available-jobs?page=3&per_page=5", headers=bearer_header("ok"))
    assert res.status_code == 200
    mock_svc.assert_called_once_with(7, 3, 5)


# ---------------------------------------------------------------------------
# GET /api/cleaner/list
# ---------------------------------------------------------------------------

def test_list_cleaners_with_cleaner_role_returns_403(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})
    res = client.get("/api/cleaner/list", headers=bearer_header("ok"))
    assert res.status_code == 403
    assert res.get_json()["error"] == "forbidden"


def test_list_cleaners_with_end_user_role_returns_200(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 9, "email": "u@test.com", "role": "end_user"})
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.list_cleaners",
        return_value=[{"user_id": 1, "name": "Cleaner A"}],
    )

    res = client.get("/api/cleaner/list", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert res.get_json() == [{"user_id": 1, "name": "Cleaner A"}]
