import os
import sqlite3
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)
CORS(app)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

DATABASE = "chat_history.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


init_database()


@app.route("/")
def home():

    return "My AI Backend is running!"


@app.route("/health")
def health():

    return {
        "status": "ok",
        "message": "Backend is working"
    }


# -----------------------------
# Create New Chat
# -----------------------------

@app.route("/new-chat", methods=["POST"])
def new_chat():

    chat_id = str(uuid.uuid4())

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO chats (id, title) VALUES (?, ?)",
        (chat_id, "New Chat")
    )

    connection.commit()
    connection.close()

    return jsonify({
        "chat_id": chat_id,
        "title": "New Chat"
    })


# -----------------------------
# Get Chat History
# -----------------------------

@app.route("/chats", methods=["GET"])
def get_chats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, created_at
        FROM chats
        ORDER BY created_at DESC
    """)

    chats = cursor.fetchall()

    connection.close()

    result = []

    for chat in chats:

        result.append({
            "id": chat[0],
            "title": chat[1],
            "created_at": chat[2]
        })

    return jsonify(result)


# -----------------------------
# Get Messages
# -----------------------------

@app.route("/chats/<chat_id>/messages", methods=["GET"])
def get_messages(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT role, message
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,))

    messages = cursor.fetchall()

    connection.close()

    result = []

    for message in messages:

        result.append({
            "role": message[0],
            "message": message[1]
        })

    return jsonify(result)


# -----------------------------
# Send Message
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400

    chat_id = data.get("chat_id")
    user_message = data.get("message", "").strip()

    if not chat_id:

        return jsonify({
            "error": "chat_id is required"
        }), 400

    if not user_message:

        return jsonify({
            "error": "Message is required"
        }), 400

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM chats WHERE id = ?",
            (chat_id,)
        )

        chat_exists = cursor.fetchone()

        connection.close()

        if not chat_exists:

            return jsonify({
                "error": "Chat not found"
            }), 404


        # Save user message

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (chat_id, role, message)
            VALUES (?, ?, ?)
            """,
            (chat_id, "user", user_message)
        )

        connection.commit()
        connection.close()


        # Get conversation history

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT role, message
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,)
        )

        history = cursor.fetchall()

        connection.close()


        contents = []

        for role, message in history:

            contents.append({
                "role": role,
                "parts": [
                    {
                        "text": message
                    }
                ]
            })


        # Gemini response

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents
        )

        ai_response = response.text


        # Save AI response

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (chat_id, role, message)
            VALUES (?, ?, ?)
            """,
            (chat_id, "model", ai_response)
        )

        connection.commit()
        connection.close()


        # Automatically create chat title

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT title FROM chats WHERE id = ?",
            (chat_id,)
        )

        current_title = cursor.fetchone()[0]

        if current_title == "New Chat":

            title = user_message[:40]

            cursor.execute(
                """
                UPDATE chats
                SET title = ?
                WHERE id = ?
                """,
                (title, chat_id)
            )

            connection.commit()

        connection.close()


        return jsonify({
            "response": ai_response
        })


    except Exception as error:

        return jsonify({
            "error": "AI request failed",
            "details": str(error)
        }), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )