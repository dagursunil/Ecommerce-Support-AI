import asyncio
import os

from dotenv import load_dotenv
from agents.mcp import MCPServerStreamableHttp, MCPToolMetaContext
from agents import (
    Agent,
    Runner,
    RunHooks,
    SQLiteSession,
    set_trace_processors,
)
from agents.memory import OpenAIResponsesCompactionSession

from customerSupportAgent.prompt import (
    SUPPORT_AGENT_INSTRUCTIONS,
)

from langsmith.integrations.openai_agents_sdk import (
    OpenAIAgentsTracingProcessor,
)

from customerSupportAgent.context import (
    PendingCheckout,
    SupportContext,
)


import json

load_dotenv()


set_trace_processors([
    OpenAIAgentsTracingProcessor()
])


class LoggingHooks(RunHooks):

    async def on_tool_start(
        self,
        context,
        agent,
        tool,
    ):
        print(f"\n[TOOL START] {tool.name}")

    async def on_tool_end(
        self,
        context,
        agent,
        tool,
        result,
    ):
        print(f"[TOOL END] {tool.name}")
        print(f"[TOOL RESULT] {result}")

        if tool.name != "place_order":
            return

        app_context: SupportContext = context.context

        try:
            # MCP result has been coming back in this shape:
            #
            # {
            #     "type": "text",
            #     "text": "{ ... JSON ... }"
            # }

            if isinstance(result, dict):
                text = result.get("text")

                if text:
                    order_result = json.loads(text)
                else:
                    return
            else:
                return

            if (
                order_result.get("success") is True
                and order_result.get("code") == "ORDER_PLACED"
            ):
                app_context.pending_checkout = None

                print(
                    "[CHECKOUT] Order completed. "
                    "Pending checkout cleared."
                )

        except (json.JSONDecodeError, TypeError):
            # We don't clear anything if we cannot confidently
            # determine that order placement succeeded.
            pass

COMMERCE_MCP_URL = os.getenv(
    "COMMERCE_MCP_URL",
    "http://localhost:8001/mcp",
)

POLICY_MCP_URL = os.getenv(
    "POLICY_MCP_URL",
    "http://localhost:8002/mcp",
)


async def main():

    def resolve_commerce_meta(
        meta_context: MCPToolMetaContext,
    ) -> dict | None:

        # We only need special metadata for order placement.
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

        # No checkout exists yet -> this is a new checkout operation.
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
            "idempotency_key": pending.idempotency_key,
        }

    async with MCPServerStreamableHttp(
        name="commerce-mcp",
        params={
            "url": COMMERCE_MCP_URL,
            "timeout": 10,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
        tool_meta_resolver=resolve_commerce_meta,
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
            model="gpt-5.6-luna",
            mcp_servers=[
                commerce_mcp,
                policy_mcp,
            ],
        )

        underlying_session = SQLiteSession(
            "customer-support-session"
        )

        session = OpenAIResponsesCompactionSession(
            session_id="customer-support-session",
            underlying_session=underlying_session,
        )

        customer_id = int(input("Customer ID: "))

        app_context = SupportContext(
            customer_id=customer_id,
        )        
        print("\nCustomer Support Agent is ready.")
        print("Type 'exit' or 'quit' to end the session.\n")

        while True:

            user_query = input("Customer: ").strip()

            if user_query.lower() in {"exit", "quit"}:
                print("Session ended.")
                break

            if not user_query:
                continue

            agent_input = f"""
            Authenticated customer context:
            customer_id={app_context.customer_id}

            Customer message:
            {user_query}
            """.strip()                
            
            result = await Runner.run(
                agent,
                agent_input,
                session=session,
                hooks=LoggingHooks(),
                context=app_context,
            )

            usage = result.context_wrapper.usage

            print(
                f"[USAGE] input={usage.input_tokens} "
                f"output={usage.output_tokens} "
                f"total={usage.total_tokens}"
            )

        # Inspect underlying session
            items = await underlying_session.get_items()

            print(f"[SESSION] stored_items={len(items)}")
            print(
                "[SESSION TYPES]",
                [item.get("type") for item in items]
            )
            

            print("\nSupport Agent:")
            print(result.final_output)
            print()


if __name__ == "__main__":
    asyncio.run(main())