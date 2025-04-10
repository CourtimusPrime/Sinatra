# python/backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from fastapi.routing import APIRoute

@pytest.fixture(scope="module")
def client():
    print("\n🔍 ROUTES AVAILABLE IN APP:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print("🛣️", route.path)
    return TestClient(app)

# RIGHT before the request
print("🧪 Sending request to /top-tracks")
response = client.get("/top-tracks", params={"user_id": "fake"})
print("📦 Got response:", response.status_code, response.text)