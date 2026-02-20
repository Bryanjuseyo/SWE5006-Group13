def test_login_success_returns_jwt(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.login_user",
        return_value={
            "message": "Login successful.",
            "token": "fake.jwt.token.that.is.long.enough",
            "user": {"id": 2, "email": "b@test.com", "role": "cleaner"}
        },
    )

    res = client.post("/api/auth/login", json={
        "email": "b@test.com",
        "password": "Passw0rd!"
    })
    assert res.status_code == 200, res.get_data(as_text=True)

    body = res.get_json()
    assert body is not None
    assert body.get("message") == "Login successful."
    assert "token" in body
    assert isinstance(body["token"], str) and len(body["token"]) > 20
    assert body["user"]["email"] == "b@test.com"


def test_login_missing_credentials_returns_401(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.login_user",
        side_effect=ValueError("invalid_credentials|Email and password are required.")
    )

    res = client.post("/api/auth/login", json={
        "email": "",
        "password": ""
    })

    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "invalid_credentials"


def test_login_wrong_password_returns_401(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.login_user",
        side_effect=ValueError("invalid_credentials|Invalid email or password.")
    )

    res = client.post("/api/auth/login", json={
        "email": "b@test.com",
        "password": "WrongPass123"
    })

    assert res.status_code == 401
    body = res.get_json()
    assert body["error"] == "invalid_credentials"


def test_login_locked_returns_423(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.login_user",
        side_effect=ValueError("locked|Too many failed attempts. Try again later.")
    )

    res = client.post("/api/auth/login", json={
        "email": "b@test.com",
        "password": "Passw0rd!"
    })

    assert res.status_code == 423
    body = res.get_json()
    assert body["error"] == "locked"
