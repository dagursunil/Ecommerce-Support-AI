import asyncio
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from agents import Agent, Runner, RunHooks
from agents.mcp import MCPServerStreamableHttp

from customerSupportAgent.prompt import (
    SUPPORT_AGENT_INSTRUCTIONS,
)


load_dotenv()


DATASET_PATH = Path(
    "evals/datasets/agent_cases.json"
)

RESULTS_PATH = Path(
    "evals/results/agent_results.json"
)


COMMERCE_MCP_URL = os.getenv(
    "COMMERCE_MCP_URL",
    "http://localhost:8001/mcp",
)

POLICY_MCP_URL = os.getenv(
    "POLICY_MCP_URL",
    "http://localhost:8002/mcp",
)


from agents import RunHooks


class EvalHooks(RunHooks):

    def __init__(self):
        self.tools_called = []
        self.tool_results = []

    async def on_tool_start(
        self,
        context,
        agent,
        tool,
    ):
        self.tools_called.append(tool.name)

    async def on_tool_end(
        self,
        context,
        agent,
        tool,
        result,
    ):
        self.tool_results.append(
            {
                "tool": tool.name,
                "result": result,
            }
        )

def load_cases() -> list[dict]:
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def evaluate_tool_selection(
    case: dict,
    tools_called: list[str],
) -> dict:

    required_tools = set(
        case.get("required_tools", [])
    )

    forbidden_tools = set(
        case.get("forbidden_tools", [])
    )

    actual_tools = set(tools_called)

    missing_tools = (
        required_tools - actual_tools
    )

    forbidden_used = (
        forbidden_tools & actual_tools
    )

    extra_tools = (
        actual_tools
        - required_tools
        - forbidden_tools
    )

    tool_selection_pass = (
        not missing_tools
        and not forbidden_used
    )

    return {
        "tool_selection_pass": tool_selection_pass,
        "missing_tools": sorted(missing_tools),
        "forbidden_tools_used": sorted(
            forbidden_used
        ),
        "extra_tools": sorted(extra_tools),
    }


async def evaluate_case(
    agent: Agent,
    case: dict,
) -> dict:

    hooks = EvalHooks()

    customer_id = case["customer_id"]

    agent_input = f"""
Authenticated customer context:
customer_id={customer_id}

Customer message:
{case["query"]}
""".strip()

    start = time.perf_counter()

    try:
        result = await Runner.run(
            agent,
            agent_input,
            hooks=hooks,
        )

        latency = time.perf_counter() - start

        tool_metrics = evaluate_tool_selection(
            case=case,
            tools_called=hooks.tools_called,
        )

        return {
            "case_id": case["id"],
            "customer_id": customer_id,
            "query": case["query"],
            "tools_called": hooks.tools_called,
            "tool_results": hooks.tool_results,
            **tool_metrics,
            "final_output": result.final_output,
            "latency_seconds": latency,
            "error": None,
        }

    except Exception as exc:

        latency = time.perf_counter() - start

        return {
            "case_id": case["id"],
            "customer_id": customer_id,
            "query": case["query"],
            "tools_called": hooks.tools_called,
            "tool_results": hooks.tool_results,
            "tool_selection_pass": False,
            "missing_tools": [],
            "forbidden_tools_used": [],
            "extra_tools": [],
            "final_output": None,
            "latency_seconds": latency,
            "error": str(exc),
        }

def calculate_summary(
    results: list[dict],
) -> dict:

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["tool_selection_pass"]
    )

    errors = sum(
        1
        for result in results
        if result["error"] is not None
    )

    total_latency = sum(
        result["latency_seconds"]
        for result in results
    )

    total_extra_tools = sum(
        len(result["extra_tools"])
        for result in results
    )

    return {
        "case_count": total,
        "tool_selection_pass_rate": (
            passed / total
            if total
            else 0.0
        ),
        "error_count": errors,
        "average_latency_seconds": (
            total_latency / total
            if total
            else 0.0
        ),
        "total_extra_tools": (
            total_extra_tools
        ),
    }


def print_case_result(
    result: dict,
) -> None:

    status = (
        "PASS"
        if result["tool_selection_pass"]
        else "FAIL"
    )

    print(
        f"\n[{status}] "
        f"{result['case_id']}"
    )

    print(
        f"Tools called: "
        f"{result['tools_called']}"
    )

    if result["missing_tools"]:
        print(
            "Missing tools:",
            result["missing_tools"],
        )

    if result["forbidden_tools_used"]:
        print(
            "Forbidden tools used:",
            result["forbidden_tools_used"],
        )

    if result["extra_tools"]:
        print(
            "Extra tools:",
            result["extra_tools"],
        )

    print(
        f"Latency: "
        f"{result['latency_seconds']:.2f}s"
    )

    if result["error"]:
        print(
            f"Error: {result['error']}"
        )


def print_summary(
    summary: dict,
) -> None:

    print("\n")
    print("=" * 80)
    print("AGENT EVALUATION SUMMARY")
    print("=" * 80)

    print(
        f"Cases: "
        f"{summary['case_count']}"
    )

    print(
        f"Tool selection pass rate: "
        f"{summary['tool_selection_pass_rate']:.3f}"
    )

    print(
        f"Errors: "
        f"{summary['error_count']}"
    )

    print(
        f"Average latency: "
        f"{summary['average_latency_seconds']:.2f}s"
    )

    print(
        f"Total extra tools: "
        f"{summary['total_extra_tools']}"
    )


def save_results(
    results: list[dict],
    summary: dict,
) -> None:

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "summary": summary,
        "cases": results,
    }

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print(
        f"\nResults saved to: "
        f"{RESULTS_PATH}"
    )


async def main():

    cases = load_cases()

    async with MCPServerStreamableHttp(
        name="commerce-mcp",
        params={
            "url": COMMERCE_MCP_URL,
            "timeout": 30,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as commerce_mcp, MCPServerStreamableHttp(
        name="policy-mcp",
        params={
            "url": POLICY_MCP_URL,
            "timeout": 60,
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

        results = []

        for case in cases:

            print("\n" + "=" * 80)
            print(
                f"Evaluating: {case['id']}"
            )
            print("=" * 80)

            result = await evaluate_case(
                agent=agent,
                case=case,
            )

            results.append(result)

            print_case_result(result)

        summary = calculate_summary(
            results
        )

        print_summary(summary)

        save_results(
            results=results,
            summary=summary,
        )


if __name__ == "__main__":
    asyncio.run(main())