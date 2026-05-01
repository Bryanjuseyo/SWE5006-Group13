import pytest
from app.services.auth_service import AuthService


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


# ---------------------------------------------------------------------------
# _password_is_valid
# ---------------------------------------------------------------------------

def test_password_too_short():
    assert AuthService._password_is_valid("Ab1") is False


def test_password_no_letter():
    assert AuthService._password_is_valid("12345678") is False


def test_password_no_digit():
    assert AuthService._password_is_valid("abcdefgh") is False


def test_password_valid():
    assert AuthService._password_is_valid("Passw0rd") is True


def test_password_none():
    assert AuthService._password_is_valid(None) is False


def test_password_exactly_eight_chars_valid():
    assert AuthService._password_is_valid("Pass1234") is True


# ---------------------------------------------------------------------------
# register_user — validation errors
# ---------------------------------------------------------------------------

def test_register_invalid_email(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_email"):
        AuthService.register_user("not-an-email", "Passw0rd1", "end_user",
                                  first_name="Jane", last_name="Doe")


def test_register_weak_password(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_password"):
        AuthService.register_user("jane@test.com", "short", "end_user",
                                  first_name="Jane", last_name="Doe")


def test_register_invalid_role(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_role"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "superuser",
                                  first_name="Jane", last_name="Doe")


def test_register_missing_first_name(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_profile"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "end_user",
                                  first_name="", last_name="Doe")


def test_register_missing_last_name(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_profile"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "end_user",
                                  first_name="Jane", last_name="")


def test_register_invalid_phone(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_phone"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "end_user",
                                  first_name="Jane", last_name="Doe",
                                  phone="12345678")


def test_register_cleaner_missing_service_type(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_cleaner_profile"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "cleaner",
                                  first_name="Jane", last_name="Doe",
                                  service_type=None)


def test_register_cleaner_invalid_service_type(mocker):
    mocker.patch("app.services.auth_service.User.query")
    with pytest.raises(ValueError, match="invalid_service_type"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "cleaner",
                                  first_name="Jane", last_name="Doe",
                                  service_type="premium")


def test_register_duplicate_email(mocker):
    mock_query = mocker.patch("app.services.auth_service.User.query")
    mock_query.filter_by.return_value.first.return_value = object()
    with pytest.raises(ValueError, match="duplicate_email"):
        AuthService.register_user("jane@test.com", "Passw0rd1", "end_user",
                                  first_name="Jane", last_name="Doe")


# ---------------------------------------------------------------------------
# register_user — success paths
# ---------------------------------------------------------------------------

def test_register_end_user_success(mocker):
    mock_query = mocker.MagicMock()
    mock_query.filter_by.return_value.first.return_value = None

    mock_session = mocker.patch("app.services.auth_service.db.session")
    mock_session.flush.return_value = None

    fake_user = mocker.MagicMock()
    fake_user.id = 42
    fake_user.email = "jane@test.com"
    mock_user_cls = mocker.patch("app.services.auth_service.User", return_value=fake_user)
    mock_user_cls.query = mock_query
    mocker.patch("app.services.auth_service.UserProfile")

    mocker.patch("app.services.auth_service.TwoFactorService.generate_and_store_otp",
                 return_value="123456")
    mocker.patch("app.services.auth_service.EmailService.send_otp_email")
    mocker.patch("app.services.auth_service.generate_2fa_temp_token",
                 return_value="tmp.token.here")

    result = AuthService.register_user("jane@test.com", "Passw0rd1", "end_user",
                                       first_name="Jane", last_name="Doe")

    assert result["requires_2fa"] is True
    assert result["temp_token"] == "tmp.token.here"


def test_register_cleaner_success(mocker):
    mock_query = mocker.MagicMock()
    mock_query.filter_by.return_value.first.return_value = None

    mock_session = mocker.patch("app.services.auth_service.db.session")
    mock_session.flush.return_value = None

    fake_user = mocker.MagicMock()
    fake_user.id = 99
    fake_user.email = "cleaner@test.com"
    mock_user_cls = mocker.patch("app.services.auth_service.User", return_value=fake_user)
    mock_user_cls.query = mock_query
    mocker.patch("app.services.auth_service.UserProfile")
    mocker.patch("app.services.auth_service.CleanerProfile")

    mocker.patch("app.services.auth_service.TwoFactorService.generate_and_store_otp",
                 return_value="654321")
    mocker.patch("app.services.auth_service.EmailService.send_otp_email")
    mocker.patch("app.services.auth_service.generate_2fa_temp_token",
                 return_value="tmp.cleaner.token")

    result = AuthService.register_user("cleaner@test.com", "Passw0rd1", "cleaner",
                                       first_name="Bob", last_name="Clean",
                                       service_type="full")

    assert result["requires_2fa"] is True
    assert result["temp_token"] == "tmp.cleaner.token"


# ---------------------------------------------------------------------------
# login_user — delegates to handler chain
# ---------------------------------------------------------------------------

def test_login_user_calls_required_credentials_handler(mocker):
    mock_handle = mocker.patch(
        "app.services.auth_service.RequiredCredentialsHandler.handle",
        return_value={"token": "jwt.token.value", "user": {}}
    )
    result = AuthService.login_user("user@test.com", "Passw0rd1")
    mock_handle.assert_called_once()
    assert result["token"] == "jwt.token.value"
