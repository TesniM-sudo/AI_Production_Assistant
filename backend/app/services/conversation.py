from app.db.database import get_connection


def create_conversation(user_id: int, title: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (user_id, title)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (user_id, title),
            )

            conversation_id = cursor.fetchone()[0]

        connection.commit()

    return conversation_id


def save_message(
    conversation_id: int,
    role: str,
    content: str,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages (
                    conversation_id,
                    role,
                    content
                )
                VALUES (%s, %s, %s);
                """,
                (
                    conversation_id,
                    role,
                    content,
                ),
            )

        connection.commit()