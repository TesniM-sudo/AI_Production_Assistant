import os
import secrets

import bcrypt

from app.db.database import get_connection


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_user(username: str, password: str):
    password_hash = hash_password(password)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (username, password_hash),
            )

            user_id = cursor.fetchone()[0]

        connection.commit()

    return user_id


def authenticate_user(username: str, password: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = %s;
                """,
                (username,),
            )

            user = cursor.fetchone()

    if not user:
        return None

    user_id, stored_username, password_hash = user

    if not verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "username": stored_username,
    }


def create_session_token():
    return secrets.token_urlsafe(32)