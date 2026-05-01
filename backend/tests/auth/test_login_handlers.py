import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.auth_login_handlers import (
    LoginContext,
    LoginHandler,
    RequiredCredentialsHandler,
    UserExistsHandler,
    BannedUserHandler,
    LockedUserHandler,
    PasswordCheckHandler,
    TwoFactorLoginHandler,
    LOCKOUT_THRESHOLD,
)


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


# ---------------------------------------------------------------------------
# LoginContext
# ---------------------------------------------------------------------------

def test_login_context_strips_and_lowercases_email():
    ctx = LoginContext("  User@TEST.com  ", "secret")
    assert ctx.email == "user@test.com"


def test_login_context_password_preserved():
    ctx = LoginContext("user@test.com", "MyPass1")
    assert ctx.password == "MyPass1"


def test_login_context_user_is_none():
    ctx = LoginContext("user@test.com", "pw")
    assert ctx.user is None


# ---------------------------------------------------------------------------
# LoginHandler
# ---------------------------------------------------------------------------

def test_login_handler_passes_to_next():
    next_h = MagicMock()
    next_h.handle.return_value = {"token": "x"}
    handler = LoginHandler(next_handler=next_h)
    ctx = LoginContext("a@b.com", "pw")
    result = handler.handle(ctx)
    next_h.handle.assert_called_once_with(ctx)
    assert result == {"token": "x"}


def test_login_handler_returns_none_with_no_next():
    handler = LoginHandler()
    ctx = LoginContext("a@b.com", "pw")
    assert handler.handle(ctx) is None


# ---------------------------------------------------------------------------
# RequiredCredentialsHandler
# ---------------------------------------------------------------------------

def test_required_credentials_raises_on_empty_email():
    handler = RequiredCredentialsHandler()
    ctx = LoginContext("", "Passw0rd1")
    with pytest.raises(ValueError, match="invalid_credentials"):
        handler.handle(ctx)


def test_required_credentials_raises_on_empty_password():
    handler = RequiredCredentialsHandler()
    ctx = LoginContext("user@test.com", "")
    with pytest.raises(ValueError, match="invalid_credentials"):
        handler.handle(ctx)


def test_required_credentials_calls_next_when_valid(mocker):
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = RequiredCredentialsHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "Passw0rd1")
    handler.handle(ctx)
    next_h.handle.assert_called_once_with(ctx)


# ---------------------------------------------------------------------------
# UserExistsHandler
# ---------------------------------------------------------------------------

def test_user_exists_raises_when_not_found(mocker):
    mocker.patch("app.services.auth_login_handlers.User.query"
                 ).filter_by.return_value.first.return_value = None
    handler = UserExistsHandler()
    ctx = LoginContext("ghost@test.com", "pw")
    with pytest.raises(ValueError, match="invalid_credentials"):
        handler.handle(ctx)


def test_user_exists_sets_context_user_and_calls_next(mocker):
    fake_user = MagicMock()
    mocker.patch("app.services.auth_login_handlers.User.query"
                 ).filter_by.return_value.first.return_value = fake_user
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = UserExistsHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "pw")
    handler.handle(ctx)
    assert ctx.user is fake_user
    next_h.handle.assert_called_once_with(ctx)


# ---------------------------------------------------------------------------
# BannedUserHandler
# ---------------------------------------------------------------------------

def test_banned_user_raises_when_banned():
    handler = BannedUserHandler()
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(is_banned=True)
    with pytest.raises(ValueError, match="banned"):
        handler.handle(ctx)


def test_banned_user_calls_next_when_not_banned():
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = BannedUserHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(is_banned=False)
    handler.handle(ctx)
    next_h.handle.assert_called_once_with(ctx)


# ---------------------------------------------------------------------------
# LockedUserHandler
# ---------------------------------------------------------------------------

def test_locked_user_raises_when_locked_in_future():
    handler = LockedUserHandler()
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    with pytest.raises(ValueError, match="locked"):
        handler.handle(ctx)


def test_locked_user_calls_next_when_lock_expired():
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = LockedUserHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(
        locked_until=datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    handler.handle(ctx)
    next_h.handle.assert_called_once_with(ctx)


def test_locked_user_calls_next_when_locked_until_is_none():
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = LockedUserHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(locked_until=None)
    handler.handle(ctx)
    next_h.handle.assert_called_once_with(ctx)


# ---------------------------------------------------------------------------
# PasswordCheckHandler
# ---------------------------------------------------------------------------

def test_password_check_increments_attempts_on_wrong_password(mocker):
    mocker.patch("app.services.auth_login_handlers.db.session")
    handler = PasswordCheckHandler()
    ctx = LoginContext("user@test.com", "wrongpw")
    ctx.user = MagicMock(
        check_password=MagicMock(return_value=False),
        failed_login_attempts=2,
        locked_until=None,
    )
    with pytest.raises(ValueError, match="invalid_credentials"):
        handler.handle(ctx)
    assert ctx.user.failed_login_attempts == 3


def test_password_check_locks_user_at_threshold(mocker):
    mocker.patch("app.services.auth_login_handlers.db.session")
    handler = PasswordCheckHandler()
    ctx = LoginContext("user@test.com", "wrongpw")
    ctx.user = MagicMock(
        check_password=MagicMock(return_value=False),
        failed_login_attempts=LOCKOUT_THRESHOLD - 1,
        locked_until=None,
    )
    with pytest.raises(ValueError, match="invalid_credentials"):
        handler.handle(ctx)
    assert ctx.user.failed_login_attempts == LOCKOUT_THRESHOLD
    assert ctx.user.locked_until is not None


def test_password_check_resets_attempts_on_correct_password(mocker):
    mocker.patch("app.services.auth_login_handlers.db.session")
    next_h = MagicMock()
    next_h.handle.return_value = None
    handler = PasswordCheckHandler(next_handler=next_h)
    ctx = LoginContext("user@test.com", "correctpw")
    ctx.user = MagicMock(
        check_password=MagicMock(return_value=True),
        failed_login_attempts=3,
        locked_until=None,
    )
    handler.handle(ctx)
    assert ctx.user.failed_login_attempts == 0
    assert ctx.user.locked_until is None
    next_h.handle.assert_called_once_with(ctx)


# ---------------------------------------------------------------------------
# TwoFactorLoginHandler
# ---------------------------------------------------------------------------

def test_two_factor_handler_skip_2fa_returns_token(mocker, app):
    app.config["SKIP_2FA"] = True
    mocker.patch("app.services.auth_login_handlers.db.session")
    mocker.patch("app.services.auth_login_handlers.generate_token",
                 return_value="jwt.access.token")

    handler = TwoFactorLoginHandler()
    ctx = LoginContext("user@test.com", "pw")
    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.email = "user@test.com"
    fake_user.role.value = "end_user"
    fake_user.to_dict.return_value = {"id": 1, "email": "user@test.com"}
    ctx.user = fake_user

    result = handler.handle(ctx)
    assert result["token"] == "jwt.access.token"
    assert "user" in result


def test_two_factor_handler_sends_otp_when_2fa_required(mocker, app):
    app.config["SKIP_2FA"] = False
    mocker.patch("app.services.auth_login_handlers.db.session")
    mocker.patch("app.services.auth_login_handlers.TwoFactorService.generate_and_store_otp",
                 return_value="112233")
    mocker.patch("app.services.auth_login_handlers.EmailService.send_otp_email")
    mocker.patch("app.services.auth_login_handlers.generate_2fa_temp_token",
                 return_value="temp.2fa.token")

    handler = TwoFactorLoginHandler()
    ctx = LoginContext("user@test.com", "pw")
    ctx.user = MagicMock(email="user@test.com")

    result = handler.handle(ctx)
    assert result["requires_2fa"] is True
    assert result["temp_token"] == "temp.2fa.token"
