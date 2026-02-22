import pytest
from app.services.cleaner_profile_service import CleanerProfileService
from app.models import ServiceType


def any_service_type_value():
    # returns the first valid enum value (e.g. "full", "partial")
    return next(iter(ServiceType)).value


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


def test_invalid_service_type_raises_value_error(mocker):
    # ensure no DB access needed for this validation test
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query.filter_by")
    mocker.patch("app.services.cleaner_profile_service.db.session")

    with pytest.raises(ValueError) as e:
        CleanerProfileService.upsert_cleaner_profile(
            user_id=1,
            data={"service_type": "invalid"}
        )

    assert "invalid_service_type" in str(e.value)


def test_negative_hourly_rate_raises_value_error(mocker):
    # create path (no existing profile)
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfile.query.filter_by",
        return_value=mocker.Mock(first=lambda: None)
    )
    mocker.patch("app.services.cleaner_profile_service.db.session")

    with pytest.raises(ValueError) as e:
        CleanerProfileService.upsert_cleaner_profile(
            user_id=1,
            data={"service_type": any_service_type_value(), "hourly_rate": -5}
        )

    assert "invalid_hourly_rate" in str(e.value)


def test_invalid_years_experience_raises_value_error(mocker):
    # create path (no existing profile)
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerProfile.query.filter_by",
        return_value=mocker.Mock(first=lambda: None)
    )
    mocker.patch("app.services.cleaner_profile_service.db.session")

    with pytest.raises(ValueError) as e:
        CleanerProfileService.upsert_cleaner_profile(
            user_id=1,
            data={"service_type": any_service_type_value(), "years_experience": -1}
        )

    assert "invalid_years_experience" in str(e.value)


def test_missing_service_type_on_create_raises_value_error(mocker):
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.first.return_value = None
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_query)

    mocker.patch("app.services.cleaner_profile_service.db.session")

    with pytest.raises(ValueError) as e:
        CleanerProfileService.upsert_cleaner_profile(user_id=1, data={})

    assert "invalid_profile" in str(e.value)
