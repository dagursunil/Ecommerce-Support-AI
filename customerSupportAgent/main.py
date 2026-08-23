import asyncio
import os

from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from customerSupportAgent.prompt import (
    SUPPORT_AGENT_INSTRUCTIONS,
)


load_dotenv()


COMMERCE_MCP_URL = os.getenv(
    "COMMERCE_MCP_URL",
    "http://localhost:8001/mcp",
)

POLICY_MCP_URL = os.getenv(
    "POLICY_MCP_URL",
    "http://localhost:8002/mcp",
)


async def main():

    async with MCPServerStreamableHttp(
        name="commerce-mcp",
        params={
            "url": COMMERCE_MCP_URL,
            "timeout": 10,
        },
    ) as commerce_mcp, MCPServerStreamableHttp(
        name="policy-mcp",
        params={
            "url": POLICY_MCP_URL,
            "timeout": 10,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as policy_mcp:

        agent = Agent(
            name="eCommerce Customer Support Agent",
            instructions=SUPPORT_AGENT_INSTRUCTIONS,
            mcp_servers=[
                commerce_mcp,
                policy_mcp,
            ],
        )

        user_query = input("\nCustomer: ")

        result = await Runner.run(
            agent,
            user_query,
        )

        print("\nSupport Agent:")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())