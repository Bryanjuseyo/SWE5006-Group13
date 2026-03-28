from app import create_app
from app.models import db as _db
import pytest
import atexit
from testcontainers.postgres import PostgresContainer as _PostgresContainer
from auth.test_routes import register_auth_test_routes
import os
import sys

# Make backend/ importable from any working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ---------------------------------------------------------------------------
# Start the test PostgreSQL container BEFORE the app is imported.
# config.py reads DATABASE_URL from the environment, so setting it here means
# Flask-SQLAlchemy will build its engine with the pg8000 URL for testing
# ---------------------------------------------------------------------------

_container = _PostgresContainer("postgres:17-alpine", driver="pg8000")
_container.start()
os.environ["DATABASE_URL"] = _container.get_connection_url()
atexit.register(_container.stop)


@pytest.fixture(scope="session")
def app():
    """Flask app wired to the test container. Schema is created once per session."""
    application = create_app()
    application.config.update(TESTING=True)

    register_auth_test_routes(application)

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_tables(app):
    """Truncate every table after each test for isolation."""
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def bearer_header():
    """
    Helper to build an Authorization header.
    Usage: headers = bearer_header("token123")
    """
    def _make(token="dummy"):
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest.fixture
def patch_decode_token(mocker):
    def _patch(payload=None, exc=None):
        targets = [
            "app.api.auth.decorators.decode_token",
            "app.api.cleaner.routes.decode_token",
        ]
        for target in targets:
            if exc is not None:
                mocker.patch(target, side_effect=exc)
            else:
                mocker.patch(target, return_value=payload or {})
    return _patch
