import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.two_factor_service import TwoFactorService
from app.models import bcrypt


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


def _mock_user(**kwargs):
    user = MagicMock()
    for key, value in kwargs.items():
        setattr(user, key, value)
    return user


# ---------------------------------------------------------------------------
# generate_and_store_otp
# ---------------------------------------------------------------------------

def test_generate_and_store_otp_returns_six_digit_string(mocker):
    mocker.patch("app.services.two_factor_service.db.session")
    user = _mock_user(two_factor_otp=None, two_factor_otp_expires=None)
    otp = TwoFactorService.generate_and_store_otp(user)
    assert isinstance(otp, str)
    assert len(otp) == 6
    assert otp.isdigit()


def test_generate_and_store_otp_stores_hash_on_user(mocker):
    mocker.patch("app.services.two_factor_service.db.session")
    user = _mock_user(two_factor_otp=None, two_factor_otp_expires=None)
    otp = TwoFactorService.generate_and_store_otp(user)
    assert user.two_factor_otp is not None
    assert bcrypt.check_password_hash(user.two_factor_otp, otp)


def test_generate_and_store_otp_sets_expiry(mocker):
    mocker.patch("app.services.two_factor_service.db.session")
    user = _mock_user(two_factor_otp=None, two_factor_otp_expires=None)
    before = datetime.now(timezone.utc)
    TwoFactorService.generate_and_store_otp(user)
    after = datetime.now(timezone.utc)
    assert user.two_factor_otp_expires > before
    assert user.two_factor_otp_expires < after + timedelta(minutes=6)


# ---------------------------------------------------------------------------
# verify_otp
# ---------------------------------------------------------------------------

def test_verify_otp_raises_when_otp_empty():
    user = _mock_user(two_factor_otp="hash", two_factor_otp_expires=datetime.now(timezone.utc))
    with pytest.raises(ValueError, match="invalid_otp"):
        TwoFactorService.verify_otp(user, "")


def test_verify_otp_raises_when_no_stored_otp():
    user = _mock_user(two_factor_otp=None, two_factor_otp_expires=None)
    with pytest.raises(ValueError, match="invalid_otp"):
        TwoFactorService.verify_otp(user, "123456")


def test_verify_otp_raises_when_no_stored_expiry():
    user = _mock_user(two_factor_otp="somehash", two_factor_otp_expires=None)
    with pytest.raises(ValueError, match="invalid_otp"):
        TwoFactorService.verify_otp(user, "123456")


def test_verify_otp_raises_when_expired():
    user = _mock_user(
        two_factor_otp="somehash",
        two_factor_otp_expires=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="expired_otp"):
        TwoFactorService.verify_otp(user, "123456")


def test_verify_otp_raises_when_hash_mismatch(app):
    with app.app_context():
        real_hash = bcrypt.generate_password_hash("999999").decode("utf-8")
    user = _mock_user(
        two_factor_otp=real_hash,
        two_factor_otp_expires=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    with pytest.raises(ValueError, match="invalid_otp"):
        TwoFactorService.verify_otp(user, "123456")


def test_verify_otp_succeeds_with_correct_otp(mocker, app):
    mocker.patch("app.services.two_factor_service.db.session")
    user = _mock_user(two_factor_otp=None, two_factor_otp_expires=None)
    otp = TwoFactorService.generate_and_store_otp(user)

    # verify_otp should not raise
    TwoFactorService.verify_otp(user, otp)
