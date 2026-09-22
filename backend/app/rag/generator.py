import requests

from app.rag.vector_store import search_documents


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "phi3:mini"


def generate_rag_answer(
    question: str,
    n_results: int = 3,
) -> dict:
    """
    Retrieve relevant document chunks and generate
    an answer using the local Ollama model.
    """

    # --------------------------------------------------------
    # 1. Retrieve relevant documents
    # --------------------------------------------------------

    retrieved_documents = search_documents(
        question,
        n_results=n_results,
    )

    if not retrieved_documents:
        return {
            "answer": "I could not find relevant information in the available documents.",
            "sources": [],
        }

    # --------------------------------------------------------
    # 2. Build context
    # --------------------------------------------------------

    context_parts = []

    for document in retrieved_documents:
        source = document.get("source", "unknown")
        text = document.get("text", "")

        context_parts.append(
            f"Source: {source}\n{text}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # --------------------------------------------------------
    # 3. Build prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI assistant for production operators.

Answer the user's question using ONLY the technical documentation
provided below.

Rules:
- Do not invent facts or procedures.
- If the answer is not supported by the documentation, say so.
- Give a concise, step-by-step answer when appropriate.
- Include only relevant safety precautions and restart conditions
  explicitly stated in the documentation.
- Preserve source names and procedure identifiers exactly.
- Do not add general knowledge.

TECHNICAL DOCUMENTATION:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    # --------------------------------------------------------
    # 4. Send prompt to local Ollama
    # --------------------------------------------------------

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 96,
                "temperature": 0.1,
            },
        },
        timeout=180,
    )

    response.raise_for_status()

    result = response.json()

    # --------------------------------------------------------
    # 5. Prepare sources
    # --------------------------------------------------------

    sources = []

    for document in retrieved_documents:
        sources.append(
            {
                "source": document.get("source"),
                "chunk_index": document.get("chunk_index"),
                "distance": document.get("distance"),
            }
        )

    return {
        "answer": result.get("response", "").strip(),
        "sources": sources,
    }
