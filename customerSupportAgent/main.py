import asyncio
import json

from dotenv import load_dotenv

from agents import (
    RunHooks,
    SQLiteSession,
    set_trace_processors,
)
from agents.memory import OpenAIResponsesCompactionSession

from langsmith.integrations.openai_agents_sdk import (
    OpenAIAgentsTracingProcessor,
)

from customerSupportAgent.context import (
    SupportContext,
)
from customerSupportAgent.service import (
    CustomerSupportAgentService,
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

        if tool.name != "place_order":
            return

        app_context: SupportContext = context.context

        try:
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

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            # Do not clear the checkout if we cannot
            # confidently determine that the order succeeded.
            pass


async def main():

    customer_id = int(
        input("Customer ID: ")
    )

    app_context = SupportContext(
        customer_id=customer_id,
    )

    # Keep existing persistent session behaviour.
    underlying_session = SQLiteSession(
        "customer-support-session"
    )

    # Keep existing session compaction behaviour.
    session = OpenAIResponsesCompactionSession(
        session_id="customer-support-session",
        underlying_session=underlying_session,
    )

    service = CustomerSupportAgentService()

    await service.start()

    try:

        print(
            "\nCustomer Support Agent is ready."
        )

        print(
            "Type 'exit' or 'quit' "
            "to end the session.\n"
        )

        while True:

            user_query = input(
                "Customer: "
            ).strip()

            if user_query.lower() in {
                "exit",
                "quit",
            }:
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

            result = await service.run(
                message=agent_input,
                app_context=app_context,
                session=session,
                hooks=LoggingHooks(),
            )

            usage = result.context_wrapper.usage

            print(
                f"[USAGE] "
                f"input={usage.input_tokens} "
                f"output={usage.output_tokens} "
                f"total={usage.total_tokens}"
            )

            # Inspect underlying session.
            items = await underlying_session.get_items()

            print(
                f"[SESSION] stored_items={len(items)}"
            )

            print(
                "[SESSION TYPES]",
                [
                    item.get("type")
                    for item in items
                ],
            )

            print("\nSupport Agent:")
            print(result.final_output)
            print()

    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())