from mcp.server import MCPServer

from policy_mcp.services.policy_service import PolicyService


mcp = MCPServer(
    name="policy-mcp",
    description="Policy retrieval services for eCommSupport-AI",
)

policy_service = PolicyService()


@mcp.tool()
def search_policy(
    query: str,
    country: str = "DE",
    top_k: int = 3,
) -> dict:
    """
    Retrieve the most relevant company policy evidence for a customer-support
    question.

    The tool returns policy text and source information. It does not generate
    the final customer-facing answer.
    """

    return policy_service.search_policy(
        query=query,
        country=country,
        top_k=top_k,
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
    )
