from api.models import LLMModel


def create_snippet(api_client, title="t1", code="x=1"):
    r = api_client.post("/api/v1/snippets/", {
        "language": "python",
        "code": code,
        "title": title
    }, format="json")
    assert r.status_code == 201
    return r.json()["id"]


def get_first_active_model_id(api_client):
    r = api_client.get("/api/v1/models/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    return data[0]["id"]


def test_create_run_ok_and_detail_contains_run(api_client):
    sid = create_snippet(api_client, code="for i in range(10): pass")
    mid = get_first_active_model_id(api_client)

    r = api_client.post("/api/v1/runs/", {"snippetId": sid, "modelId": mid},
                        format="json")
    assert r.status_code == 201
    run = r.json()
    assert run["snippet"] == sid
    assert run["model"]["id"] == mid
    assert run["status"] in ("ok", "error", "timeout", "rate_limited")
    # Mock client should produce explanation & complexity fields
    if run["status"] == "ok":
        assert isinstance(run["response_text"], str)
        assert run["complexity_time"]
        assert run["complexity_space"]

    # Detail should list the run
    d = api_client.get(f"/api/v1/snippets/{sid}/").json()
    assert len(d["runs"]) == 1
    assert d["runs"][0]["id"] == run["id"]


def test_run_invalid_ids(api_client):
    # Non-existent snippet
    mid = get_first_active_model_id(api_client)
    r = api_client.post("/api/v1/runs/", {"snippetId": 999999, "modelId": mid},
                        format="json")
    assert r.status_code == 400

    # Non-existent model
    sid = create_snippet(api_client)
    r = api_client.post("/api/v1/runs/", {"snippetId": sid, "modelId": 999999},
                        format="json")
    assert r.status_code == 400


def test_feedback_upsert_and_range_validation(api_client):
    sid = create_snippet(api_client)
    mid = get_first_active_model_id(api_client)
    run = api_client.post("/api/v1/runs/", {"snippetId": sid, "modelId": mid},
                          format="json").json()

    # Invalid score
    bad = api_client.post("/api/v1/feedback/", {"run": run["id"], "score": 101},
                          format="json")
    assert bad.status_code == 400

    # Valid create
    ok = api_client.post("/api/v1/feedback/",
                         {"run": run["id"], "score": 25, "comment": "nice"},
                         format="json")
    assert ok.status_code == 201
    assert ok.json()["score"] == 25

    # Update (upsert)
    again = api_client.post("/api/v1/feedback/",
                            {"run": run["id"], "score": -10}, format="json")
    assert again.status_code == 201
    assert again.json()["score"] == -10

    # The run detail should now include feedback
    detail = api_client.get(f"/api/v1/snippets/{sid}/").json()
    assert detail["runs"][0]["feedback"]["score"] == -10
