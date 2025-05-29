from api.models import Snippet


def test_create_snippet_and_fetch_detail(api_client):
    payload = {
        "language": "python",
        "code": "def add(a,b):\n    return a+b",
        "options_json": {"tests": True},
        "title": "Simple add"
    }
    r = api_client.post("/api/v1/snippets/", payload, format="json")
    assert r.status_code == 201
    sid = r.json()["id"]

    # Detail should include empty runs for now
    r2 = api_client.get(f"/api/v1/snippets/{sid}/")
    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == sid
    assert body["language"] == "python"
    assert body["code"].startswith("def add")
    assert isinstance(body["runs"], list)
    assert body["runs"] == []


def test_snippets_list_recent_limit(api_client):
    # Create a few snippets
    for i in range(25):
        api_client.post("/api/v1/snippets/", {
            "language": "python",
            "code": f"print({i})",
            "title": f"s{i}"
        }, format="json")

    r = api_client.get("/api/v1/snippets/?limit=20")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 20
    # Ordered by id desc -> first is the newest
    first_id = items[0]["id"]
    second_id = items[1]["id"]
    assert first_id > second_id
