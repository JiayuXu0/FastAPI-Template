"""Unit tests for password utility helpers."""

import pytest

from utils import password

pytestmark = pytest.mark.unit


def test_get_password_hash_and_verify_roundtrip():
    """Password hashes should verify for the original secret and reject others."""
    secret = "SuperSecret!"

    hashed = password.get_password_hash(secret)

    assert hashed != secret
    assert password.verify_password(secret, hashed)
    assert not password.verify_password("NotTheSame", hashed)


def test_generate_password_uses_passlib(monkeypatch):
    """The password generator should delegate to passlib's helper."""
    monkeypatch.setattr(password.pwd, "genword", lambda: "generated")

    assert password.generate_password() == "generated"
