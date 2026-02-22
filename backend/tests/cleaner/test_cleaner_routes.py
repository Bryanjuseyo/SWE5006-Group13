def test_cleaner_dashboard_returns_200(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})

    res = client.get("/api/cleaner/dashboard", headers=bearer_header("ok"))
    assert res.status_code == 200
    assert res.get_json()["message"] == "Cleaner dashboard"


def test_cleaner_get_profile_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.get_cleaner_profile",
        return_value={"user_id": 7, "skills": ["kitchen"]},
    )

    res = client.get("/api/cleaner/profile", headers=bearer_header("ok"))
    assert res.status_code == 200
    body = res.get_json()
    assert body["user_id"] == 7
    assert body["skills"] == ["kitchen"]


def test_cleaner_update_profile_success(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.upsert_cleaner_profile",
        return_value={"user_id": 7, "pricing": 50},
    )

    res = client.put(
        "/api/cleaner/profile",
        headers=bearer_header("ok"),
        json={"pricing": 50},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["user_id"] == 7
    assert body["pricing"] == 50


def test_cleaner_update_profile_value_error_returns_400(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})

    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.upsert_cleaner_profile",
        side_effect=ValueError("invalid_input|Bad data"),
    )

    res = client.put(
        "/api/cleaner/profile",
        headers=bearer_header("ok"),
        json={"pricing": -1},
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_input"
    assert body["message"] == "Bad data"


def test_cleaner_update_profile_missing_json_defaults_empty_dict(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 7, "email": "c@test.com", "role": "cleaner"})

    upsert = mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfileService.upsert_cleaner_profile",
        return_value={"ok": True},
    )

    # no JSON body (request.get_json(silent=True) -> None, then `or {}` makes it {})
    res = client.put("/api/cleaner/profile", headers=bearer_header("ok"))
    assert res.status_code == 200

    upsert.assert_called_once()
    assert upsert.call_args[0][0] == 7      # user_id
    assert upsert.call_args[0][1] == {}     # data
