def test_register_success(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        return_value={
            "message": "Registration successful.",
            "user": {"id": 1, "email": "a@test.com", "role": "end_user"}
        },
    )

    res = client.post("/api/auth/register", json={
        "email": "a@test.com",
        "password": "Passw0rd!",
        "role": "end_user"
    })
    assert res.status_code == 201, res.get_data(as_text=True)

    body = res.get_json()
    assert body is not None
    assert body["user"]["email"] == "a@test.com"

def test_register_invalid_email_returns_400(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        side_effect=ValueError("invalid_email|Invalid email format.")
    )

    res = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "Passw0rd!",
        "role": "end_user"
    })

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_email"


def test_register_weak_password_returns_400(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        side_effect=ValueError(
            "invalid_password|Password must be at least 8 characters and contain letters and numbers.")
    )

    res = client.post("/api/auth/register", json={
        "email": "a@test.com",
        "password": "123",   # weak
        "role": "end_user"
    })

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_password"


def test_register_invalid_role_returns_400(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        side_effect=ValueError("invalid_role|Role must be one of: end_user, cleaner, administrator.")
    )

    res = client.post("/api/auth/register", json={
        "email": "a@test.com",
        "password": "Passw0rd!",
        "role": "superman"
    })

    assert res.status_code == 400
    body = res.get_json()
    assert body["error"] == "invalid_role"


def test_register_duplicate_email_returns_409(client, mocker):
    mocker.patch(
        "app.services.auth_service.AuthService.register_user",
        side_effect=ValueError("duplicate_email|Email is already registered.")
    )

    res = client.post("/api/auth/register", json={
        "email": "a@test.com",
        "password": "Passw0rd!",
        "role": "end_user"
    })

    assert res.status_code == 409
    body = res.get_json()
    assert body["error"] == "duplicate_email"