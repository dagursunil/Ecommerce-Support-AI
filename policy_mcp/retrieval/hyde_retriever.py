import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "ecomm-policy",
)

EMBEDDING_MODEL = "text-embedding-3-small"
HYDE_MODEL = "gpt-4o-mini"

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

pinecone = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pinecone.Index(
    PINECONE_INDEX_NAME
)

def generate_hypothetical_answer(
    query: str,
) -> str:

    response = openai_client.responses.create(
        model=HYDE_MODEL,
        instructions="""
You are generating hypothetical text only for document retrieval.

Given a customer support policy question, write a short passage
that could plausibly appear in the relevant company policy.

Do not answer conversationally.
Do not claim that the generated text is the real company policy.
Focus on terminology and concepts likely to appear in the
relevant policy document.
""".strip(),
        input=query,
    )

    return response.output_text

def create_embedding(
    text: str,
) -> list[float]:

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding

def search_policy_hyde(
    query: str,
    top_k: int = 3,
    country: str | None = None,
) -> dict:

    hypothetical_document = (
        generate_hypothetical_answer(query)
    )

    query_vector = create_embedding(
        hypothetical_document
    )

    metadata_filter = None

    if country:
        metadata_filter = {
            "country": {
                "$eq": country
            }
        }

    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=metadata_filter,
    )

    results = []

    for match in response.matches:
        results.append(
            {
                "chunk_id": match.id,
                "score": match.score,
                "text": match.metadata.get("text"),
                "country": match.metadata.get("country"),
                "policy_version": match.metadata.get(
                    "policy_version"
                ),
                "source_document": match.metadata.get(
                    "source_document"
                ),
            }
        )

    return {
        "query": query,
        "hypothetical_document": hypothetical_document,
        "results": results,
    }

if __name__ == "__main__":

    result = search_policy_hyde(
        query="Can I return a damaged laptop after 45 days?",
        top_k=3,
        country="DE",
    )

    print("\n===== ORIGINAL QUERY =====")
    print(result["query"])

    print("\n===== HYPOTHETICAL DOCUMENT =====")
    print(result["hypothetical_document"])

    print("\n===== RETRIEVED CHUNKS =====")

    for chunk in result["results"]:
        print("\n" + "=" * 80)
        print("Chunk:", chunk["chunk_id"])
        print("Score:", chunk["score"])
        print("Source:", chunk["source_document"])
        print("-" * 80)
        print(chunk["text"])