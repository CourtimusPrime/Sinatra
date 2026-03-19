"""Smoke test to verify the test setup works."""

import pytest


@pytest.mark.asyncio
async def test_root_returns_ok(client):
    resp = await client.get("/")
    assert resp.status_code == 200
