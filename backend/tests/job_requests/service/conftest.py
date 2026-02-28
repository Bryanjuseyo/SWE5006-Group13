"""
Shared fixtures for job request service tests.
"""
import pytest


FUTURE_DATE = "2099-12-31"
PAST_DATE = "2020-01-01"

REQUIRED_FIELDS = {
    "title": "House cleaning",
    "service_type": "full",
    "location": "123 Ang Mo Kio Street",
    "preferred_date": FUTURE_DATE,
}


@pytest.fixture(autouse=True)
def _app_context(app):
    """Push an application context for every service test."""
    with app.app_context():
        yield

@pytest.fixture
def make_user(app):
    from app.models import db, User, UserRole

    def _make(email="u@test.com", role=UserRole.end_user, password_hash="x", **kwargs):
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            **kwargs,
        )
        db.session.add(user)
        db.session.commit()
        return user

    return _make