"""Unit tests for JWT helper functions."""

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from schemas.login import JWTPayload
from utils import jwt as jwt_utils

pytestmark = pytest.mark.unit

TEST_SECRET = "test-secret-key-32-characters-long!!"


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Ensure deterministic cryptographic settings during tests."""
    monkeypatch.setattr(jwt_utils.settings, "SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr(jwt_utils.settings, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(jwt_utils.settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    monkeypatch.setattr(jwt_utils.settings, "JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7)


def _decode_token(token: str) -> dict:
    """Decode a token without enforcing expiration checks."""
    return pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"], options={"verify_exp": False})


def test_create_access_token_encodes_expected_payload():
    payload = JWTPayload(
        user_id=1,
        username="alice",
        is_superuser=False,
        exp=datetime.now(UTC) + timedelta(minutes=10),
    )

    token = jwt_utils.create_access_token(data=payload)
    decoded = _decode_token(token)

    assert decoded["user_id"] == 1
    assert decoded["username"] == "alice"
    assert decoded["token_type"] == "access"


def test_create_refresh_token_sets_refresh_type():
    token = jwt_utils.create_refresh_token(user_id=7, username="bob", is_superuser=True)
    decoded = _decode_token(token)

    assert decoded["token_type"] == "refresh"
    assert decoded["user_id"] == 7
    assert decoded["username"] == "bob"


def test_verify_token_enforces_token_type():
    payload = {
        "user_id": 2,
        "username": "carol",
        "is_superuser": False,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "token_type": "access",
    }
    token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

    with pytest.raises(pyjwt.InvalidTokenError):
        jwt_utils.verify_token(token, token_type="refresh")


def test_verify_token_rejects_expired_tokens():
    payload = {
        "user_id": 2,
        "username": "dave",
        "is_superuser": False,
        "exp": datetime.now(UTC) - timedelta(seconds=1),
        "token_type": "access",
    }
    token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

    with pytest.raises(pyjwt.ExpiredSignatureError):
        jwt_utils.verify_token(token)


def test_create_token_pair_produces_distinct_tokens():
    access_token, refresh_token = jwt_utils.create_token_pair(
        user_id=5, username="erin", is_superuser=False
    )

    assert access_token != refresh_token
    assert _decode_token(access_token)["token_type"] == "access"
    assert _decode_token(refresh_token)["token_type"] == "refresh"
