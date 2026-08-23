from policy_mcp.retrieval.adaptive_retriever import (
    search_policy_adaptive,
)


class PolicyService:

    def search_policy(
        self,
        query: str,
        country: str = "DE",
        top_k: int = 3,
    ) -> dict:

        if not query.strip():
            return {
                "success": False,
                "code": "INVALID_QUERY",
                "message": "Policy query cannot be empty.",
            }

        if top_k <= 0:
            return {
                "success": False,
                "code": "INVALID_TOP_K",
                "message": "top_k must be greater than zero.",
            }

        result = search_policy_adaptive(
            query=query,
            country=country,
            top_k=min(top_k, 10),
        )

        return {
            "success": True,
            "code": "POLICY_EVIDENCE_FOUND",
            "strategy": result["strategy"],
            "count": len(result["results"]),
            "results": result["results"],
        }