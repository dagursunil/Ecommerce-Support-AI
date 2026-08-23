import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def run():
    async with streamable_http_client(
        "http://localhost:8002/mcp"
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("\n===== AVAILABLE TOOLS =====")

            for tool in tools.tools:
                print(tool.name)

            result = await session.call_tool(
                "search_policy",
                arguments={
                    "query": "Can I return a damaged laptop after 45 days?",
                    "country": "DE",
                    "top_k": 3,
                },
            )

            print("\n===== POLICY RESULT =====")
            print(result)


if __name__ == "__main__":
    asyncio.run(run())