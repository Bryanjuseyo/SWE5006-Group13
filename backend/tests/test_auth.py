def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "email": "a@test.com",
        "password": "Passw0rd!",
        "role": "END_USER"
    })
    assert res.status_code == 201
    body = res.get_json()
    assert "id" in body
    assert body["email"] == "a@test.com"


def test_login_success_returns_jwt(client):
    res = client.post("/api/auth/register", json={
        "email": "b@test.com",
        "password": "Passw0rd!",
        "role": "CLEANER"
    })
    assert res.status_code == 201

    res = client.post("/api/auth/login", json={
        "email": "b@test.com",
        "password": "Passw0rd!"
    })
    assert res.status_code == 200
    body = res.get_json()
    assert "access_token" in body  # contract
