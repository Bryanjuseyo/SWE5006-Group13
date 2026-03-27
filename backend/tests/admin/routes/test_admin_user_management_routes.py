# tests/admin/routes/test_admin_user_management_routes.py

def test_admin_ban_user_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.ban_user",
        return_value={
            "message": "User has been banned.",
            "user": {
                "id": 7,
                "email": "user@test.com",
                "role": "end_user",
                "is_banned": True,
            },
        },
    )

    res = client.patch(
        "/api/admin/users/7/ban",
        json={"reason": "Malicious activity"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "User has been banned."
    assert body["user"]["id"] == 7
    assert body["user"]["is_banned"] is True


def test_admin_ban_user_not_found(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.ban_user",
        side_effect=ValueError("not_found|User not found."),
    )

    res = client.patch(
        "/api/admin/users/999/ban",
        json={"reason": "Malicious activity"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"
    assert body["message"] == "User not found."


def test_admin_ban_user_forbidden_for_admin_target(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.ban_user",
        side_effect=ValueError("forbidden|Cannot ban an administrator."),
    )

    res = client.patch(
        "/api/admin/users/1/ban",
        json={"reason": "Should fail"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "forbidden"
    assert body["message"] == "Cannot ban an administrator."


def test_admin_ban_user_already_banned(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.ban_user",
        side_effect=ValueError("already_banned|User is already banned."),
    )

    res = client.patch(
        "/api/admin/users/7/ban",
        json={"reason": "Duplicate ban"},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "already_banned"
    assert body["message"] == "User is already banned."


def test_admin_ban_user_without_reason(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    ban_mock = mocker.patch(
        "app.services.admin_service.AdminService.ban_user",
        return_value={
            "message": "User has been banned.",
            "user": {
                "id": 8,
                "email": "enduser@test.com",
                "role": "end_user",
                "is_banned": True,
            },
        },
    )

    res = client.patch(
        "/api/admin/users/8/ban",
        json={},
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    ban_mock.assert_called_once_with(8, reason=None)