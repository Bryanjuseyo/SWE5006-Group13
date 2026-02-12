def test_end_user_dashboard_success(client, patch_decode_token, bearer_header):
    patch_decode_token(payload={
        "user_id": 20,
        "email": "user@test.com",
        "role": "end_user",
    })

    res = client.get("/api/end-user/dashboard", headers=bearer_header("ok"))
    assert res.status_code == 200

    body = res.get_json()
    assert body["message"] == "Welcome end-user user@test.com"
