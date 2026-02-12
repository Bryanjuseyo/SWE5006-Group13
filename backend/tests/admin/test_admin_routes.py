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
