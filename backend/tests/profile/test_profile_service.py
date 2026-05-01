import pytest
from datetime import datetime, timezone
from app.services.profile_service import ProfileService


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


def _mock_upq(mocker, first_return):
    """Patch UserProfile.query so filter_by(...).first() returns first_return."""
    mock_upq = mocker.MagicMock()
    mock_upq.filter_by.return_value.first.return_value = first_return
    mocker.patch("app.services.profile_service.UserProfile.query", new=mock_upq)
    return mock_upq


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------

def test_get_profile_returns_dict_with_expected_keys(mocker):
    mock_user = mocker.MagicMock()
    mock_user.email = "test@test.com"
    mock_user.role.value = "end_user"
    mock_user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

    mock_profile = mocker.MagicMock()
    mock_profile.to_dict.return_value = {"first_name": "Alice", "last_name": "Smith"}

    mock_uq = mocker.MagicMock()
    mock_uq.get.return_value = mock_user
    mocker.patch("app.services.profile_service.User.query", new=mock_uq)
    _mock_upq(mocker, mock_profile)

    result = ProfileService.get_profile(1)

    assert result["email"] == "test@test.com"
    assert result["role"] == "end_user"
    assert "created_at" in result
    assert result["profile"] == {"first_name": "Alice", "last_name": "Smith"}


def test_get_profile_returns_none_profile_when_no_user_profile(mocker):
    mock_user = mocker.MagicMock()
    mock_user.email = "noone@test.com"
    mock_user.role.value = "cleaner"
    mock_user.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)

    mock_uq = mocker.MagicMock()
    mock_uq.get.return_value = mock_user
    mocker.patch("app.services.profile_service.User.query", new=mock_uq)
    _mock_upq(mocker, None)

    result = ProfileService.get_profile(99)

    assert result["profile"] is None


# ---------------------------------------------------------------------------
# upsert_profile
# ---------------------------------------------------------------------------

def test_upsert_profile_invalid_phone_raises_value_error(mocker):
    mocker.patch("app.services.profile_service.db.session")
    _mock_upq(mocker, mocker.MagicMock())

    with pytest.raises(ValueError) as exc_info:
        ProfileService.upsert_profile(1, {"phone": "12345678"})

    assert "invalid_phone" in str(exc_info.value)


def test_upsert_profile_missing_names_on_create_raises_value_error(mocker):
    mocker.patch("app.services.profile_service.db.session")
    _mock_upq(mocker, None)

    with pytest.raises(ValueError) as exc_info:
        ProfileService.upsert_profile(1, {"city": "Singapore"})

    assert "invalid_profile" in str(exc_info.value)


def test_upsert_profile_creates_new_profile_when_none_exists(mocker):
    mock_session = mocker.patch("app.services.profile_service.db.session")

    mock_profile_instance = mocker.MagicMock()
    mock_profile_instance.to_dict.return_value = {"first_name": "Alice", "last_name": "Smith"}

    mock_up_cls = mocker.patch(
        "app.services.profile_service.UserProfile",
        return_value=mock_profile_instance,
    )
    mock_up_cls.query.filter_by.return_value.first.return_value = None

    result = ProfileService.upsert_profile(1, {"first_name": "Alice", "last_name": "Smith"})

    mock_session.add.assert_called_once_with(mock_profile_instance)
    mock_session.commit.assert_called_once()
    assert result["message"] == "Profile updated."
    assert result["profile"]["first_name"] == "Alice"


def test_upsert_profile_updates_existing_profile(mocker):
    mock_session = mocker.patch("app.services.profile_service.db.session")

    mock_existing = mocker.MagicMock()
    mock_existing.to_dict.return_value = {"first_name": "Bob", "city": "Tampines"}

    _mock_upq(mocker, mock_existing)

    result = ProfileService.upsert_profile(2, {"city": "Tampines"})

    mock_session.commit.assert_called_once()
    assert result["message"] == "Profile updated."
