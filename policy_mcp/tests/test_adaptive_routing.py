from policy_mcp.retrieval import adaptive_retriever


def test_uses_simple_when_simple_is_good(monkeypatch):

    def fake_simple(*args, **kwargs):
        return [
            {"chunk_id": "c1", "score": 0.72, "text": "A"},
            {"chunk_id": "c2", "score": 0.61, "text": "B"},
        ]

    def fail_hyde(*args, **kwargs):
        raise AssertionError("HyDE should not be called")

    def fail_multi_query(*args, **kwargs):
        raise AssertionError("Multi-query should not be called")

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy",
        fake_simple,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_hyde",
        fail_hyde,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_multi_query",
        fail_multi_query,
    )

    result = adaptive_retriever.search_policy_adaptive(
        query="What is the return period?",
        country="DE",
        top_k=3,
    )

    assert result["strategy"] == "simple"
    assert result["results"][0]["chunk_id"] == "c1"

def test_escalates_to_hyde_when_simple_is_weak(monkeypatch):

    def fake_simple(*args, **kwargs):
        return [
            {"chunk_id": "c1", "score": 0.48, "text": "A"},
            {"chunk_id": "c2", "score": 0.40, "text": "B"},
        ]

    def fake_hyde(*args, **kwargs):
        return {
            "query": "test",
            "hypothetical_document": "hypothetical answer",
            "results": [
                {"chunk_id": "c3", "score": 0.75, "text": "C"},
                {"chunk_id": "c4", "score": 0.66, "text": "D"},
            ],
        }

    def fail_multi_query(*args, **kwargs):
        raise AssertionError("Multi-query should not be called")

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy",
        fake_simple,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_hyde",
        fake_hyde,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_multi_query",
        fail_multi_query,
    )

    result = adaptive_retriever.search_policy_adaptive(
        query="Can I return a damaged laptop after 45 days?",
        country="DE",
        top_k=3,
    )

    assert result["strategy"] == "hyde"
    assert result["results"][0]["chunk_id"] == "c3"

def test_escalates_to_multi_query_when_simple_and_hyde_are_weak(
    monkeypatch,
):

    def fake_simple(*args, **kwargs):
        return [
            {"chunk_id": "c1", "score": 0.42, "text": "A"},
            {"chunk_id": "c2", "score": 0.35, "text": "B"},
        ]

    def fake_hyde(*args, **kwargs):
        return {
            "query": "test",
            "hypothetical_document": "hypothetical answer",
            "results": [
                {"chunk_id": "c3", "score": 0.54, "text": "C"},
                {"chunk_id": "c4", "score": 0.47, "text": "D"},
            ],
        }

    def fake_multi_query(*args, **kwargs):
        return {
            "original_query": "test",
            "generated_queries": [
                "query 1",
                "query 2",
                "query 3",
            ],
            "results": [
                {"chunk_id": "c5", "score": 0.69, "text": "E"},
                {"chunk_id": "c6", "score": 0.62, "text": "F"},
            ],
        }

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy",
        fake_simple,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_hyde",
        fake_hyde,
    )

    monkeypatch.setattr(
        adaptive_retriever,
        "search_policy_multi_query",
        fake_multi_query,
    )

    result = adaptive_retriever.search_policy_adaptive(
        query="Some difficult policy question",
        country="DE",
        top_k=3,
    )

    assert result["strategy"] == "multi_query"
    assert result["results"][0]["chunk_id"] == "c5"   