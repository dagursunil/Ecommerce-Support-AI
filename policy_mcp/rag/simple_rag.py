import os

from dotenv import load_dotenv
from openai import OpenAI

from policy_mcp.retrieval.simple_retriever import search_policy


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY)


def answer_policy_question(
    query: str,
    country: str = "DE",
    top_k: int = 3,
) -> dict:

    retrieved_chunks = search_policy(
        query=query,
        top_k=top_k,
        country=country,
    )

    if not retrieved_chunks:
        return {
            "success": False,
            "code": "NO_RELEVANT_POLICY_FOUND",
            "answer": (
                "I could not find enough policy information "
                "to answer this question."
            ),
            "sources": [],
        }

    context = "\n\n".join(
        [
            f"""
SOURCE {index}
Document: {chunk['source_document']}
Policy Version: {chunk['policy_version']}
Similarity Score: {chunk['score']}

{chunk['text']}
""".strip()
            for index, chunk in enumerate(
                retrieved_chunks,
                start=1,
            )
        ]
    )

    system_prompt = """
You are a customer-support policy assistant.

Answer the user's question using only the supplied policy context.

Rules:
- Do not invent policy rules.
- If the supplied context is insufficient, say so clearly.
- If different retrieved passages contain conditions or exceptions,
  mention those conditions.
- Do not treat similarity scores as confidence percentages.
- Keep the answer concise and customer-friendly.
""".strip()

    user_prompt = f"""
USER QUESTION:
{query}

POLICY CONTEXT:
{context}
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        input=user_prompt,
    )

    return {
        "success": True,
        "code": "POLICY_ANSWER_GENERATED",
        "answer": response.output_text,
        "sources": [
            {
                "chunk_id": chunk["chunk_id"],
                "score": chunk["score"],
                "source_document": chunk["source_document"],
                "policy_version": chunk["policy_version"],
            }
            for chunk in retrieved_chunks
        ],
    }


if __name__ == "__main__":
    result = answer_policy_question(
        "Can I return a damaged laptop after 45 days?"
    )

    print("\n===== ANSWER =====")
    print(result["answer"])

    print("\n===== SOURCES =====")
    for source in result["sources"]:
        print(source)