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


def test_add_availability_success(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = []

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    mock_slot = mocker.Mock()
    mock_slot.to_dict.return_value = {
        "id": 1,
        "cleaner_profile_id": 10,
        "start_date": "2026-03-20",
        "end_date": "2026-03-20",
        "start_time": "09:00",
        "end_time": "12:00",
    }

    mock_cleaner_availability = mocker.patch(
        "app.services.cleaner_profile_service.CleanerAvailability",
        return_value=mock_slot
    )

    mock_session = mocker.patch("app.services.cleaner_profile_service.db.session")

    result = CleanerProfileService.add_availability(
        user_id=1,
        data={
            "start_date": "2026-03-20",
            "end_date": "2026-03-20",
            "start_time": "09:00",
            "end_time": "12:00",
        }
    )

    mock_profile_query.filter_by.assert_called_once_with(user_id=1)
    mock_cleaner_availability.assert_called_once()
    mock_session.add.assert_called_once_with(mock_slot)
    mock_session.commit.assert_called_once()
    assert result["message"] == "Availability slot added."
    assert result["availability"]["cleaner_profile_id"] == 10


def test_add_availability_missing_start_date_raises_value_error(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = []

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    with pytest.raises(ValueError) as e:
        CleanerProfileService.add_availability(
            user_id=1,
            data={
                "end_date": "2026-03-20",
                "start_time": "09:00",
                "end_time": "12:00",
            }
        )

    assert "start_date is required" in str(e.value)


def test_add_availability_invalid_date_range_raises_value_error(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = []

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    with pytest.raises(ValueError) as e:
        CleanerProfileService.add_availability(
            user_id=1,
            data={
                "start_date": "2026-03-21",
                "end_date": "2026-03-20",
                "start_time": "09:00",
                "end_time": "12:00",
            }
        )

    assert "end_date must be on or after start_date" in str(e.value)


def test_add_availability_end_time_without_start_time_raises_value_error(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = []

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    with pytest.raises(ValueError) as e:
        CleanerProfileService.add_availability(
            user_id=1,
            data={
                "start_date": "2026-03-20",
                "end_date": "2026-03-20",
                "end_time": "12:00",
            }
        )

    assert "start_time is required when end_time is set" in str(e.value)


def test_add_availability_invalid_time_range_raises_value_error(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = []

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    with pytest.raises(ValueError) as e:
        CleanerProfileService.add_availability(
            user_id=1,
            data={
                "start_date": "2026-03-20",
                "end_date": "2026-03-20",
                "start_time": "12:00",
                "end_time": "09:00",
            }
        )

    assert "end_time must be after start_time" in str(e.value)


def test_add_availability_overlapping_slot_raises_value_error(mocker):
    existing_slot = mocker.Mock()
    existing_slot.start_date = __import__("datetime").date(2026, 3, 20)
    existing_slot.end_date = __import__("datetime").date(2026, 3, 20)
    existing_slot.start_time = __import__("datetime").time(9, 0)
    existing_slot.end_time = __import__("datetime").time(12, 0)

    mock_profile = mocker.Mock()
    mock_profile.id = 10
    mock_profile.availability = [existing_slot]

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    with pytest.raises(ValueError) as e:
        CleanerProfileService.add_availability(
            user_id=1,
            data={
                "start_date": "2026-03-20",
                "end_date": "2026-03-20",
                "start_time": "10:00",
                "end_time": "11:00",
            }
        )

    assert "overlaps with an existing availability slot" in str(e.value)


def test_update_availability_success(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10

    existing_other_slot = mocker.Mock()
    existing_other_slot.id = 99
    existing_other_slot.start_date = __import__("datetime").date(2026, 3, 25)
    existing_other_slot.end_date = __import__("datetime").date(2026, 3, 25)
    existing_other_slot.start_time = __import__("datetime").time(14, 0)
    existing_other_slot.end_time = __import__("datetime").time(16, 0)

    slot_to_update = mocker.Mock()
    slot_to_update.id = 1
    slot_to_update.cleaner_profile_id = 10
    slot_to_update.to_dict.return_value = {
        "id": 1,
        "cleaner_profile_id": 10,
        "start_date": "2026-03-20",
        "end_date": "2026-03-20",
        "start_time": "08:00",
        "end_time": "10:00",
    }

    mock_profile.availability = [slot_to_update, existing_other_slot]

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    mock_availability_query = mocker.Mock()
    mock_availability_query.filter_by.return_value.first.return_value = slot_to_update
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerAvailability.query",
        mock_availability_query
    )

    mock_session = mocker.patch("app.services.cleaner_profile_service.db.session")

    result = CleanerProfileService.update_availability(
        user_id=1,
        availability_id=1,
        data={
            "start_date": "2026-03-20",
            "end_date": "2026-03-20",
            "start_time": "08:00",
            "end_time": "10:00",
        }
    )

    mock_profile_query.filter_by.assert_called_once_with(user_id=1)
    mock_availability_query.filter_by.assert_called_once_with(id=1, cleaner_profile_id=10)
    mock_session.commit.assert_called_once()
    assert result["message"] == "Availability slot updated."
    assert result["availability"]["id"] == 1


def test_delete_availability_success(mocker):
    mock_profile = mocker.Mock()
    mock_profile.id = 10

    slot = mocker.Mock()
    slot.id = 1
    slot.cleaner_profile_id = 10

    mock_profile_query = mocker.Mock()
    mock_profile_query.filter_by.return_value.first.return_value = mock_profile
    mocker.patch("app.services.cleaner_profile_service.CleanerProfile.query", mock_profile_query)

    mock_availability_query = mocker.Mock()
    mock_availability_query.filter_by.return_value.first.return_value = slot
    mocker.patch(
        "app.services.cleaner_profile_service.CleanerAvailability.query",
        mock_availability_query
    )

    mock_session = mocker.patch("app.services.cleaner_profile_service.db.session")

    result = CleanerProfileService.delete_availability(user_id=1, availability_id=1)

    mock_profile_query.filter_by.assert_called_once_with(user_id=1)
    mock_availability_query.filter_by.assert_called_once_with(id=1, cleaner_profile_id=10)
    mock_session.delete.assert_called_once_with(slot)
    mock_session.commit.assert_called_once()
    assert result["message"] == "Availability slot removed."
