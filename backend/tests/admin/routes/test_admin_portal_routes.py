def test_admin_dashboard_success(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    res = client.get("/api/admin/dashboard", headers=bearer_header("ok"))

    assert res.status_code == 200
    body = res.get_json()
    assert body["message"] == "Welcome admin admin@test.com"


def test_admin_stats_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={
        "user_id": 10,
        "email": "admin@test.com",
        "role": "administrator",
    })

    mocker.patch(
        "app.services.admin_service.AdminService.get_dashboard_stats",
        return_value={
            "users": {
                "total": 5,
                "end_users": 2,
                "cleaners": 2,
                "administrators": 1,
                "banned": 1,
            },
            "jobs": {
                "total": 6,
                "pending": 1,
                "confirmed": 1,
                "in_progress": 1,
                "completed": 1,
                "cancelled": 1,
                "rejected": 1,
            },
        },
    )

    res = client.get("/api/admin/stats", headers=bearer_header("ok"))

    assert res.status_code == 200
    body = res.get_json()

    assert body["users"]["total"] == 5
    assert body["users"]["end_users"] == 2
    assert body["users"]["cleaners"] == 2
    assert body["users"]["administrators"] == 1
    assert body["users"]["banned"] == 1

    assert body["jobs"]["total"] == 6
    assert body["jobs"]["pending"] == 1
    assert body["jobs"]["confirmed"] == 1
    assert body["jobs"]["in_progress"] == 1
    assert body["jobs"]["completed"] == 1
    assert body["jobs"]["cancelled"] == 1
    assert body["jobs"]["rejected"] == 1


def test_admin_dashboard_forbidden_for_non_admin(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "user@test.com",
        "role": "end_user",
    })

    res = client.get("/api/admin/dashboard", headers=bearer_header("ok"))

    assert res.status_code == 403


def test_admin_stats_forbidden_for_non_admin(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "cleaner@test.com",
        "role": "cleaner",
    })

    res = client.get("/api/admin/stats", headers=bearer_header("ok"))

    assert res.status_code == 403


def test_admin_dashboard_unauthorized_without_token(client):
    res = client.get("/api/admin/dashboard")

    assert res.status_code == 401


def test_admin_stats_unauthorized_without_token(client):
    res = client.get("/api/admin/stats")

    assert res.status_code == 401
