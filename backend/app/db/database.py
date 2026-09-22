import os

import psycopg


DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    return psycopg.connect(DATABASE_URL)


def initialize_database():

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id)
                        ON DELETE CASCADE,
                    title VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER
                        REFERENCES conversations(id)
                        ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        connection.commit()


def create_conversation(
    user_id=None,
    title="New conversation",
):
    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO conversations
                    (user_id, title)
                VALUES
                    (%s, %s)
                RETURNING id;
                """,
                (user_id, title),
            )

            conversation_id = cursor.fetchone()[0]

        connection.commit()

    return conversation_id


def save_message(
    conversation_id,
    role,
    content,
):
    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO messages
                    (conversation_id, role, content)
                VALUES
                    (%s, %s, %s)
                RETURNING id;
                """,
                (
                    conversation_id,
                    role,
                    content,
                ),
            )

            message_id = cursor.fetchone()[0]

        connection.commit()

    return message_id