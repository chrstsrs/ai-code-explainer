import json


def test_models_list_seeds_and_returns_active_models(api_client):
    # First call seeds defaults in ModelsListView if empty
    resp = api_client.get("/api/v1/models/")
    assert resp.status_code == 200
    data = resp.json()
    # Should contain at least the defaults you configured
    names = [m["name"] for m in data]
    assert "openai:gpt-4o-mini" in names
    assert "openai:gpt-3.5" in names
    assert "anthropic:claude-3-haiku" in names
    assert "mock:demo" in names
