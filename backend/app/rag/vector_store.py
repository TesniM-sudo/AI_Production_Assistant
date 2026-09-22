from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

DOCUMENTS_DIR = Path("/srv/ai-data/documents")
CHROMA_DIR = Path("/srv/ai-data/chroma")

COLLECTION_NAME = "production_documents"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# Initialize ChromaDB and embedding model
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    local_files_only=True,
)


# ============================================================
# Text chunking
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks.

    chunk_size:
        Maximum number of characters per chunk.

    overlap:
        Number of characters repeated between chunks.
    """

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ============================================================
# Index documents
# ============================================================

def index_documents() -> Dict:
    """
    Read documents from /srv/ai-data/documents,
    create chunks, generate embeddings,
    and store them in ChromaDB.
    """

    documents = []

    for file_path in DOCUMENTS_DIR.iterdir():

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in [".txt", ".pdf"]:
            continue

        # ----------------------------------------------------
        # Read TXT files
        # ----------------------------------------------------

        if file_path.suffix.lower() == ".txt":

            text = file_path.read_text(
                encoding="utf-8"
            )

        # ----------------------------------------------------
        # Read PDF files
        # ----------------------------------------------------

        elif file_path.suffix.lower() == ".pdf":

            import fitz

            pdf = fitz.open(file_path)

            pages = []

            for page in pdf:
                pages.append(page.get_text())

            pdf.close()

            text = "\n".join(pages)

        else:
            continue

        text = text.strip()

        if not text:
            continue

        # ----------------------------------------------------
        # Create chunks
        # ----------------------------------------------------

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):

            documents.append(
                {
                    "id": f"{file_path.name}-{index}",
                    "text": chunk,
                    "source": file_path.name,
                    "chunk_index": index,
                }
            )

    if not documents:
        return {
            "status": "no_documents",
            "indexed": 0,
        }

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    texts = [
        document["text"]
        for document in documents
    ]

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True
    )

    # --------------------------------------------------------
    # Store in ChromaDB
    # --------------------------------------------------------

    collection.upsert(
        ids=[
            document["id"]
            for document in documents
        ],

        documents=texts,

        embeddings=embeddings.tolist(),

        metadatas=[
            {
                "source": document["source"],
                "chunk_index": document["chunk_index"],
            }
            for document in documents
        ],
    )

    return {
        "status": "success",
        "indexed": len(documents),
        "collection": COLLECTION_NAME,
    }


# ============================================================
# Search documents
# ============================================================

def search_documents(
    query: str,
    n_results: int = 3
) -> List[Dict]:
    """
    Search ChromaDB for documents
    semantically similar to the query.
    """

    if not query.strip():
        return []

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=n_results,
    )

    documents = results.get("documents", [[]])[0]

    metadatas = results.get("metadatas", [[]])[0]

    distances = results.get("distances", [[]])[0]

    retrieved = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved.append(
            {
                "text": document,
                "source": metadata.get("source"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": distance,
            }
        )

    return retrieved