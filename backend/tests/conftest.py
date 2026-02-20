import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def bearer_header():
    """
    Helper to build Authorization header.
    Usage: headers = bearer_header("token123")
    """
    def _make(token="dummy"):
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest.fixture
def patch_decode_token(mocker):
    """
    Patch app.api.auth.decorators.decode_token because decorators.py imported it directly.

    Usage:
      patch_decode_token(payload={...})
      patch_decode_token(exc=ExpiredSignatureError())
    """
    def _patch(payload=None, exc=None):
        target = "app.api.auth.decorators.decode_token"
        if exc is not None:
            mocker.patch(target, side_effect=exc)
        else:
            mocker.patch(target, return_value=payload or {})
    return _patch
