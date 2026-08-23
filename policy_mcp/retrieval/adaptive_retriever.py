from policy_mcp.retrieval.simple_retriever import search_policy
from policy_mcp.retrieval.hyde_retriever import search_policy_hyde
from policy_mcp.retrieval.multi_query_retriever import (
    search_policy_multi_query,
)


SIMPLE_TOP_SCORE_THRESHOLD = 0.60
SIMPLE_SECOND_SCORE_THRESHOLD = 0.50

HYDE_TOP_SCORE_THRESHOLD = 0.65
HYDE_SECOND_SCORE_THRESHOLD = 0.55


def retrieval_is_good(
    results: list[dict],
    top_threshold: float,
    second_threshold: float,
) -> bool:

    if len(results) < 2:
        return False

    return (
        results[0]["score"] >= top_threshold
        and results[1]["score"] >= second_threshold
    )


def search_policy_adaptive(
    query: str,
    country: str | None = None,
    top_k: int = 3,
) -> dict:

    # 1. Cheapest path first
    simple_results = search_policy(
        query=query,
        top_k=top_k,
        country=country,
    )

    if retrieval_is_good(
        simple_results,
        top_threshold=SIMPLE_TOP_SCORE_THRESHOLD,
        second_threshold=SIMPLE_SECOND_SCORE_THRESHOLD,
    ):
        return {
            "strategy": "simple",
            "results": simple_results,
        }

    # 2. Escalate to HyDE
    hyde_result = search_policy_hyde(
        query=query,
        top_k=top_k,
        country=country,
    )

    hyde_results = hyde_result["results"]

    if retrieval_is_good(
        hyde_results,
        top_threshold=HYDE_TOP_SCORE_THRESHOLD,
        second_threshold=HYDE_SECOND_SCORE_THRESHOLD,
    ):
        return {
            "strategy": "hyde",
            "results": hyde_results,
        }

    # 3. Final escalation for broader recall
    multi_query_result = search_policy_multi_query(
        query=query,
        top_k_per_query=top_k,
        final_top_k=top_k,
        country=country,
    )

    return {
        "strategy": "multi_query",
        "results": multi_query_result["results"],
    }