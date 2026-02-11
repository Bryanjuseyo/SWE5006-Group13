def register_and_login(client, mocker, email, role):
    # mock register
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        return_value={
            "message": "Registration successful.",
            "user": {"id": 123, "email": email, "role": role}
        }
    )

    # mock login
    mocker.patch(
        "app.services.auth_service.AuthService.login_user",
        return_value={
            "message": "Login successful.",
            "token": "fake.jwt.token.that.is.long.enough",
            "user": {"id": 123, "email": email, "role": role}
        }
    )

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
    assert body and "token" in body, f"missing token: {body}"
    return body["token"]


VALID_ROLES = {"end_user", "cleaner", "administrator"}


def test_assign_role_requires_authentication(client):
    # No Authorization header
    res = client.put("/api/admin/users/123/role", json={"role": "cleaner"})
    # When implemented, should be 401 (not 404)
    assert res.status_code == 401


def test_non_admin_cannot_assign_roles(client, mocker):
    token = register_and_login(client, mocker, "user@test.com", "end_user")

    res = client.put(
        "/api/admin/users/123/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "administrator"}
    )
    assert res.status_code == 403


def test_admin_can_assign_roles(client, mocker):
    admin_token = register_and_login(client, mocker, "admin@test.com", "administrator")

    res = client.put(
        "/api/admin/users/123/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "cleaner"}
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body is not None
    assert body.get("message") in ("Role updated.", "Role update successful.")
    assert "user" in body
    assert body["user"]["id"] == 123
    assert body["user"]["role"] == "cleaner"


def test_admin_assign_invalid_role_returns_400(client, mocker):
    admin_token = register_and_login(client, mocker, "admin@test.com", "administrator")

    res = client.put(
        "/api/admin/users/123/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "superman"}  # invalid
    )

    assert res.status_code == 400
    body = res.get_json()
    assert body is not None
    assert body.get("error") == "invalid_role"


def test_admin_assign_role_user_not_found_returns_404(client, mocker):
    admin_token = register_and_login(client, mocker, "admin@test.com", "administrator")

    res = client.put(
        "/api/admin/users/999999/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "cleaner"}
    )

    assert res.status_code == 404
    body = res.get_json()
    assert body is not None
    assert body.get("error") in ("not_found", "user_not_found")
