"""Integration test specific fixtures and markers."""

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session", autouse=True)
async def _ensure_database(setup_database):
    """Ensure the test database is initialised for integration tests only."""
    yield
