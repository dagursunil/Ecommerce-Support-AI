import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def run():
    async with streamable_http_client(
        "http://localhost:8001/mcp"
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
                "check_order_status",
                arguments={
                    "customer_id": 2,
                    "order_number": "ORD-2026-000002",
                },
            )

            print("\n===== TOOL RESULT =====")
            print(f"Order status: {result}")

            # list_customer_orders
            result = await session.call_tool(
                "list_customer_orders",
                arguments={
                    "customer_id": 1,
                    "limit": 10,
                },
            )
            print(f"List of orders: {result}")

            # search_products
            result = await session.call_tool(
                "search_products",
                arguments={
                    "category": "Laptop",
                    "max_price": 1500,
                    "in_stock_only": True,
                    "limit": 10,
                },
            )
            print(f"Search results: {result}")

            # get_product_details
            result = await session.call_tool(
                "get_product_details",
                arguments={
                    "product_id": 2,
                },
            )
            print(f"Product details: {result}")

            result = await session.call_tool(
                "get_warranty_details",
                arguments={
                    "customer_id": 1,
                    "order_number": "ORD-2026-000001",
                    "product_id": 2,
                },
            )
            print(f"Warranty details: {result}")

            result = await session.call_tool(
                "place_order",
                arguments={
                    "customer_id": 1,
                    "product_id": 6,
                    "quantity": 1,
                    "address_id": 1,
                    "idempotency_key": "TEST-ORDER-001",
                },
            )

            print("\n===== PLACE ORDER =====")
            print(result)


if __name__ == "__main__":
    asyncio.run(run())