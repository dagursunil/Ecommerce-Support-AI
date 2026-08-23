from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from policy_mcp.ingestion.extract_pdf import (
    PDF_PATH,
    extract_pdf_text,
)


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def chunk_text(text: str) -> list[str]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    return splitter.split_text(text)

def build_policy_chunks(
    text: str,
) -> list[dict]:

    raw_chunks = chunk_text(text)

    policy_chunks = []

    for index, chunk in enumerate(raw_chunks, start=1):
        policy_chunks.append(
            {
                "chunk_id": f"return_policy_de_2026-{index:04d}",
                "text": chunk,
                "metadata": {
                    "country": "DE",
                    "policy_version": "2026.1",
                    "source_document": "return_policy_de_2026.pdf",
                },
            }
        )

    return policy_chunks


if __name__ == "__main__":

    text = extract_pdf_text(PDF_PATH)

    chunks = build_policy_chunks(text)

    print("Total chunks:", len(chunks))

    for chunk in chunks[:5]:
        print("\n" + "=" * 80)
        print("Chunk ID:", chunk["chunk_id"])
        print("Metadata:", chunk["metadata"])
        print("-" * 80)
        print(chunk["text"])