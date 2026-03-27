def test_admin_reject_booking_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.reject_booking",
        return_value={
            "message": "Booking has been rejected.",
            "job_request": {
                "id": 7,
                "title": "Suspicious Booking",
                "status": "rejected",
            },
        },
    )

    res = client.patch(
        "/api/admin/bookings/7/reject",
        json={"reason": "Suspicious pattern"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Booking has been rejected."
    assert body["job_request"]["id"] == 7
    assert body["job_request"]["status"] == "rejected"


def test_admin_reject_booking_without_reason(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    reject_mock = mocker.patch(
        "app.services.admin_service.AdminService.reject_booking",
        return_value={
            "message": "Booking has been rejected.",
            "job_request": {
                "id": 8,
                "title": "Suspicious Booking",
                "status": "rejected",
            },
        },
    )

    res = client.patch(
        "/api/admin/bookings/8/reject",
        json={},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    reject_mock.assert_called_once_with(8, reason=None)


def test_admin_reject_booking_not_found(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.reject_booking",
        side_effect=ValueError("not_found|Job request not found."),
    )

    res = client.patch(
        "/api/admin/bookings/999/reject",
        json={"reason": "Suspicious activity"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"
    assert body["message"] == "Job request not found."


def test_admin_reject_booking_invalid_status(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.reject_booking",
        side_effect=ValueError(
            "invalid_status|Cannot reject a completed or already rejected booking."
        ),
    )

    res = client.patch(
        "/api/admin/bookings/7/reject",
        json={"reason": "Suspicious activity"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_status"
    assert body["message"] == "Cannot reject a completed or already rejected booking."


def test_admin_reject_booking_forbidden_for_non_admin(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "user@test.com",
        "role": "end_user",
    })

    res = client.patch(
        "/api/admin/bookings/7/reject",
        json={"reason": "Suspicious activity"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 403


def test_admin_reject_booking_unauthorized_without_token(client):
    res = client.patch(
        "/api/admin/bookings/7/reject",
        json={"reason": "Suspicious activity"},
    )

    assert res.status_code == 401
