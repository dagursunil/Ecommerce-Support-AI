import asyncio
import os

from dotenv import load_dotenv
from agents.mcp import MCPServerStreamableHttp
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
        cache_tools_list=True,
        max_retry_attempts=3,
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
        session_context = {
            "customer_id": customer_id
        }        
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
            customer_id={session_context["customer_id"]}

            Customer message:
            {user_query}
            """.strip()                
            
            result = await Runner.run(
                agent,
                agent_input,
                session=session,
                hooks=LoggingHooks(),
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