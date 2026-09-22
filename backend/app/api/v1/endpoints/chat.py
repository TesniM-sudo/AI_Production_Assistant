from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.generator import generate_rag_answer
from app.services.auth import authenticate_user
from app.services.conversation import (
    create_conversation,
    save_message,
)


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    message: str
    n_results: int = 3
    username: str
    password: str


@router.post("")
def chat(request: ChatRequest):
    """
    Process a user question using the RAG pipeline
    and store the conversation in PostgreSQL.
    """

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    user = authenticate_user(
        request.username,
        request.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    try:
        # Create a conversation for this interaction.
        conversation_id = create_conversation(
            user_id=user["id"],
            title=request.message[:100],
        )

        # Save the user's question.
        save_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        # Run RAG + local LLM.
        result = generate_rag_answer(
            question=request.message,
            n_results=request.n_results,
        )

        # Save the AI answer.
        save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
        )

        return {
            "user_id": user["id"],
            "username": user["username"],
            "conversation_id": conversation_id,
            "message": request.message,
            "answer": result["answer"],
            "sources": result["sources"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(exc)}",
        )