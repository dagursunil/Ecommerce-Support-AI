from policy_mcp.retrieval.adaptive_retriever import (
    search_policy_adaptive,
)


def test_adaptive_retriever_returns_results():
    result = search_policy_adaptive(
        query="Can I return a damaged laptop after 45 days?",
        country="DE",
        top_k=3,
    )

    assert result["strategy"] in {
        "simple",
        "hyde",
        "multi_query",
    }

    assert len(result["results"]) > 0

    first = result["results"][0]

    assert "chunk_id" in first
    assert "score" in first
    assert "text" in first
    assert "source_document" in first
    assert "policy_version" in first

def test_adaptive_retriever_strategy_for_complex_query():
    result = search_policy_adaptive(
        query="Can I return a damaged laptop after 45 days?",
        country="DE",
        top_k=3,
    )

    print(
        "\nSelected strategy:",
        result["strategy"],
    )

    for item in result["results"]:
        print(
            item["chunk_id"],
            item["score"],
        )

    assert result["strategy"] in {
        "simple",
        "hyde",
        "multi_query",
    }