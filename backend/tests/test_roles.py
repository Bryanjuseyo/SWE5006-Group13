def register_and_login(client, email, role):
    r1 = client.post("/api/auth/register", json={
        "email": email,
        "password": "Passw0rd!",
        "role": role
    })
    assert r1.status_code == 201, f"register failed: {r1.status_code} {r1.get_data(as_text=True)}"

    r2 = client.post("/api/auth/login", json={
        "email": email,
        "password": "Passw0rd!"
    })
    assert r2.status_code == 200, f"login failed: {r2.status_code} {r2.get_data(as_text=True)}"

    body = r2.get_json()
    assert body and "access_token" in body, f"missing access_token: {body}"
    return body["access_token"]


def test_non_admin_cannot_assign_roles(client):
    token = register_and_login(client, "user@test.com", "END_USER")

    res = client.put("/api/admin/users/123/role",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"role": "ADMIN"}
                     )
    assert res.status_code == 403


def test_admin_can_assign_roles(client):
    admin_token = register_and_login(client, "admin@test.com", "ADMIN")

    res = client.put("/api/admin/users/123/role",
                     headers={"Authorization": f"Bearer {admin_token}"},
                     json={"role": "CLEANER"}
                     )
    # depends on whether user exists
    assert res.status_code in (200, 404)
