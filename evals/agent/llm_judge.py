from pydantic import BaseModel, Field
from agents import Agent, Runner


class JudgeResult(BaseModel):
    score: int = Field(
        ge=1,
        le=5,
        description="Overall quality score from 1 to 5.",
    )

    passed: bool

    groundedness: int = Field(
        ge=1,
        le=5,
    )

    correctness: int = Field(
        ge=1,
        le=5,
    )

    completeness: int = Field(
        ge=1,
        le=5,
    )

    unsupported_claims: bool

    reason: str


JUDGE_INSTRUCTIONS = """
You are an evaluator for an e-commerce customer support AI agent.

Your job is to evaluate the agent's final answer against:

1. The customer's query.
2. The retrieved tool evidence.
3. The evaluation criteria supplied for this test case.

Important rules:

- Treat tool results as the authoritative evidence.
- Do not reward claims that are unsupported by the tool evidence.
- Do not assume facts that are not present in the evidence.
- A response may be concise and still be complete.
- Do not judge writing style unless it affects correctness or usefulness.
- If the answer promises a refund, repair, replacement, warranty coverage,
  return eligibility, order placement, or other outcome without sufficient
  evidence, mark unsupported_claims=true.
- Score groundedness, correctness, and completeness from 1 to 5.
- passed should normally be true only when the answer is grounded,
  substantially correct, and satisfies the supplied criteria.
"""


judge_agent = Agent(
    name="Customer Support Eval Judge",
    instructions=JUDGE_INSTRUCTIONS,
    output_type=JudgeResult,
)


async def judge_response(
    query: str,
    criteria: list[str],
    tool_results: list[dict],
    final_output: str,
) -> JudgeResult:

    criteria_text = "\n".join(
        f"- {criterion}"
        for criterion in criteria
    )

    evidence_text = "\n\n".join(
        f"TOOL: {item['tool']}\n"
        f"RESULT:\n{item['result']}"
        for item in tool_results
    )

    judge_input = f"""
CUSTOMER QUERY
--------------
{query}


EVALUATION CRITERIA
-------------------
{criteria_text}


TOOL EVIDENCE
-------------
{evidence_text}


AGENT FINAL ANSWER
------------------
{final_output}


Evaluate the final answer strictly against the evidence and criteria.
""".strip()

    result = await Runner.run(
        judge_agent,
        judge_input,
    )

    return result.final_output