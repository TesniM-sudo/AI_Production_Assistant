from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth import authenticate_user


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(request: LoginRequest):

    user = authenticate_user(
        username=request.username,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    return {
        "status": "success",
        "user_id": user["id"],
        "username": user["username"],
    }