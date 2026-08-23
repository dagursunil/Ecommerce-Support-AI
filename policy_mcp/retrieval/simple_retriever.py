import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "ecomm-policy",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"

openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone = Pinecone(api_key=PINECONE_API_KEY)

index = pinecone.Index(PINECONE_INDEX_NAME)


def create_query_embedding(query: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )

    return response.data[0].embedding


def search_policy(
    query: str,
    top_k: int = 3,
    country: str | None = None,
) -> list[dict]:

    query_vector = create_query_embedding(query)

    metadata_filter = None

    if country:
        metadata_filter = {
            "country": {"$eq": country}
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

    return results

if __name__ == "__main__":

    query = "Can I return a damaged laptop after 45 days?"

    results = search_policy(
        query=query,
        top_k=3,
        country="DE",
    )

    for result in results:
        print("\n" + "=" * 80)
        print("Chunk:", result["chunk_id"])
        print("Score:", result["score"])
        print("Source:", result["source_document"])
        print("-" * 80)
        print(result["text"])