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
MULTI_QUERY_MODEL = "gpt-4o-mini"

openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone = Pinecone(api_key=PINECONE_API_KEY)
index = pinecone.Index(PINECONE_INDEX_NAME)

def generate_query_variations(
    query: str,
) -> list[str]:

    response = openai_client.responses.create(
        model=MULTI_QUERY_MODEL,
        instructions="""
Rewrite the user's policy question into exactly three
different search queries.

Preserve the original meaning, but vary the wording and
emphasize different aspects of the question.

Return only the three queries, one per line.
Do not number them.
""".strip(),
        input=query,
    )

    queries = [
        line.strip()
        for line in response.output_text.splitlines()
        if line.strip()
    ]

    return queries[:3]

def create_embedding(text: str) -> list[float]:

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding

def search_policy_multi_query(
    query: str,
    top_k_per_query: int = 3,
    final_top_k: int = 5,
    country: str | None = None,
) -> dict:

    generated_queries = generate_query_variations(query)

    metadata_filter = None

    if country:
        metadata_filter = {
            "country": {
                "$eq": country
            }
        }

    merged_results = {}

    for generated_query in generated_queries:

        query_vector = create_embedding(
            generated_query
        )

        response = index.query(
            vector=query_vector,
            top_k=top_k_per_query,
            include_metadata=True,
            filter=metadata_filter,
        )

        for match in response.matches:

            existing = merged_results.get(match.id)

            result = {
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
                "matched_query": generated_query,
            }

            # Same chunk may be retrieved by several queries.
            # Keep the strongest similarity score we observed.
            if (
                existing is None
                or match.score > existing["score"]
            ):
                merged_results[match.id] = result

    ranked_results = sorted(
        merged_results.values(),
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "original_query": query,
        "generated_queries": generated_queries,
        "results": ranked_results[:final_top_k],
    }

if __name__ == "__main__":

    result = search_policy_multi_query(
        query="Can I return a damaged laptop after 45 days?",
        top_k_per_query=3,
        final_top_k=5,
        country="DE",
    )

    print("\n===== ORIGINAL QUERY =====")
    print(result["original_query"])

    print("\n===== GENERATED QUERIES =====")
    for query in result["generated_queries"]:
        print("-", query)

    print("\n===== RETRIEVED CHUNKS =====")

    for chunk in result["results"]:
        print("\n" + "=" * 80)
        print("Chunk:", chunk["chunk_id"])
        print("Score:", chunk["score"])
        print("Matched Query:", chunk["matched_query"])
        print("Source:", chunk["source_document"])
        print("-" * 80)
        print(chunk["text"])