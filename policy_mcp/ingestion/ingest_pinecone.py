import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from policy_mcp.ingestion.extract_pdf import (
    PDF_PATH,
    extract_pdf_text,
)
from policy_mcp.ingestion.chunk_text import (
    build_policy_chunks,
)


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "ecomm-policy",
)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

pinecone = Pinecone(
    api_key=PINECONE_API_KEY
)

def ensure_index():

    existing_indexes = [
        index.name
        for index in pinecone.list_indexes()
    ]

    if PINECONE_INDEX_NAME not in existing_indexes:
        pinecone.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )

def create_embedding(text: str) -> list[float]:

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding

def ingest_policy():

    text = extract_pdf_text(PDF_PATH)

    chunks = build_policy_chunks(text)

    ensure_index()

    index = pinecone.Index(
        PINECONE_INDEX_NAME
    )

    vectors = []

    for chunk in chunks:

        embedding = create_embedding(
            chunk["text"]
        )

        metadata = {
            **chunk["metadata"],
            "text": chunk["text"],
        }

        vectors.append(
            {
                "id": chunk["chunk_id"],
                "values": embedding,
                "metadata": metadata,
            }
        )

    index.upsert(
        vectors=vectors
    )

    print(
        f"Ingested {len(vectors)} policy chunks"
    )

if __name__ == "__main__":
    ingest_policy()