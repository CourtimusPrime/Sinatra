# backend/tests/conftest.py
# Shared setup for all tests — defines fixtures like your client

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
