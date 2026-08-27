import os
from contextlib import AsyncExitStack

from agents import Agent, Runner
from agents.mcp import (
    MCPServerStreamableHttp,
    MCPToolMetaContext,
)
from dotenv import load_dotenv

load_dotenv()

from customerSupportAgent.context import (
    PendingCheckout,
    SupportContext,
)
from customerSupportAgent.prompt import (
    SUPPORT_AGENT_INSTRUCTIONS,
)


COMMERCE_MCP_URL = os.getenv(
    "COMMERCE_MCP_URL",
    "http://localhost:8001/mcp",
)

POLICY_MCP_URL = os.getenv(
    "POLICY_MCP_URL",
    "http://localhost:8002/mcp",
)


def resolve_commerce_meta(
    meta_context: MCPToolMetaContext,
) -> dict | None:

    if meta_context.tool_name != "place_order":
        return None

    app_context: SupportContext = (
        meta_context.run_context.context
    )

    args = meta_context.arguments or {}

    product_id = args["product_id"]
    quantity = args["quantity"]
    address_id = args["address_id"]

    pending = app_context.pending_checkout

    if pending is None:
        pending = PendingCheckout(
            product_id=product_id,
            quantity=quantity,
            address_id=address_id,
        )

        app_context.pending_checkout = pending

    print(
        "[IDEMPOTENCY]",
        pending.idempotency_key,
    )

    return {
        "idempotency_key":
            pending.idempotency_key,
    }


class CustomerSupportAgentService:

    def __init__(self):
        self._stack = AsyncExitStack()
        self.agent: Agent | None = None

    async def start(self):

        commerce_mcp = await self._stack.enter_async_context(
            MCPServerStreamableHttp(
                name="commerce-mcp",
                params={
                    "url": COMMERCE_MCP_URL,
                    "timeout": 30,
                },
                cache_tools_list=True,
                max_retry_attempts=3,
                tool_meta_resolver=resolve_commerce_meta,
            )
        )

        policy_mcp = await self._stack.enter_async_context(
            MCPServerStreamableHttp(
                name="policy-mcp",
                params={
                    "url": POLICY_MCP_URL,
                    "timeout": 60,
                },
                cache_tools_list=True,
                max_retry_attempts=3,
            )
        )

        self.agent = Agent(
            name="eCommerce Customer Support Agent",
            instructions=SUPPORT_AGENT_INSTRUCTIONS,
            mcp_servers=[
                commerce_mcp,
                policy_mcp,
            ],
        )

    async def stop(self):
        await self._stack.aclose()

    async def run(
        self,
        message: str,
        app_context: SupportContext,
        *,
        session=None,
        hooks=None,
    ):

        if self.agent is None:
            raise RuntimeError(
                "CustomerSupportAgentService has not been started."
            )

        return await Runner.run(
            self.agent,
            message,
            context=app_context,
            session=session,
            hooks=hooks,
        )