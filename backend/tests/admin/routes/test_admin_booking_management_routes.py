def test_admin_get_bookings_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.get_all_bookings",
        return_value={
            "job_requests": [
                {
                    "id": 1,
                    "title": "Kitchen Cleaning",
                    "status": "pending",
                },
                {
                    "id": 2,
                    "title": "Bathroom Cleaning",
                    "status": "confirmed",
                },
            ]
        },
    )

    res = client.get("/api/admin/bookings", headers=bearer_header("ok"))

    assert res.status_code == 200
    body = res.get_json()
    assert len(body["job_requests"]) == 2
    assert body["job_requests"][0]["title"] == "Kitchen Cleaning"
    assert body["job_requests"][1]["status"] == "confirmed"


def test_admin_get_bookings_with_filters(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    bookings_mock = mocker.patch(
        "app.services.admin_service.AdminService.get_all_bookings",
        return_value={"job_requests": []},
    )

    res = client.get(
        "/api/admin/bookings?status=confirmed&search=kitchen",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    bookings_mock.assert_called_once_with(
        status_filter="confirmed",
        search="kitchen",
        page=1,
        per_page=25,
    )


def test_admin_get_bookings_invalid_status(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.get_all_bookings",
        side_effect=ValueError(
            "invalid_status|status must be one of: pending, confirmed, in_progress, completed, cancelled, rejected."
        ),
    )

    res = client.get(
        "/api/admin/bookings?status=bad_status",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_status"
    assert "status must be one of" in body["message"]


def test_admin_get_bookings_forbidden_for_non_admin(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "user@test.com",
        "role": "end_user",
    })

    res = client.get("/api/admin/bookings", headers=bearer_header("ok"))

    assert res.status_code == 403


def test_admin_get_bookings_unauthorized_without_token(client):
    res = client.get("/api/admin/bookings")

    assert res.status_code == 401
