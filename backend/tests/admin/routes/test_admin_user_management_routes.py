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


def test_admin_get_users_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.get_all_users",
        return_value={
            "users": [
                {
                    "id": 1,
                    "email": "user1@test.com",
                    "role": "end_user",
                    "is_banned": False,
                    "profile": None,
                },
                {
                    "id": 2,
                    "email": "cleaner1@test.com",
                    "role": "cleaner",
                    "is_banned": True,
                    "profile": {
                        "first_name": "John",
                        "last_name": "Tan",
                    },
                },
            ]
        },
    )

    res = client.get("/api/admin/users", headers=bearer_header("ok"))

    assert res.status_code == 200
    body = res.get_json()
    assert len(body["users"]) == 2
    assert body["users"][0]["email"] == "user1@test.com"
    assert body["users"][1]["is_banned"] is True


def test_admin_get_users_with_filters(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    users_mock = mocker.patch(
        "app.services.admin_service.AdminService.get_all_users",
        return_value={"users": []},
    )

    res = client.get(
        "/api/admin/users?role=cleaner&banned=true&search=john",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    users_mock.assert_called_once_with(
        role_filter="cleaner",
        banned_filter="true",
        search="john",
    )


def test_admin_get_users_invalid_role(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.get_all_users",
        side_effect=ValueError("invalid_role|role must be one of: end_user, cleaner, administrator."),
    )

    res = client.get(
        "/api/admin/users?role=bad_role",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_role"
    assert "role must be one of" in body["message"]


def test_admin_unban_user_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.unban_user",
        return_value={
            "message": "User has been unbanned.",
            "user": {
                "id": 7,
                "email": "user@test.com",
                "role": "end_user",
                "is_banned": False,
            },
        },
    )

    res = client.patch(
        "/api/admin/users/7/unban",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "User has been unbanned."
    assert body["user"]["id"] == 7
    assert body["user"]["is_banned"] is False


def test_admin_unban_user_not_found(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.unban_user",
        side_effect=ValueError("not_found|User not found."),
    )

    res = client.patch(
        "/api/admin/users/999/unban",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 404
    body = res.get_json()
    assert body["error"] == "not_found"
    assert body["message"] == "User not found."


def test_admin_unban_user_not_banned(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.unban_user",
        side_effect=ValueError("not_banned|User is not banned."),
    )

    res = client.patch(
        "/api/admin/users/7/unban",
        headers=bearer_header("ok"),
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "not_banned"
    assert body["message"] == "User is not banned."


def test_admin_get_users_forbidden_for_non_admin(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "user@test.com",
        "role": "end_user",
    })

    res = client.get("/api/admin/users", headers=bearer_header("ok"))

    assert res.status_code == 403


def test_admin_get_users_unauthorized_without_token(client):
    res = client.get("/api/admin/users")

    assert res.status_code == 401
