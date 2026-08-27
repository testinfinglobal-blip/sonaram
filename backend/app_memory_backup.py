import os
import sqlite3

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


# -----------------------------
# Database
# -----------------------------

def init_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_message(role, message):

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO messages (role, message) VALUES (?, ?)",
        (role, message)
    )

    connection.commit()
    connection.close()


def get_history():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT role, message
        FROM messages
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


# Database initialize
init_database()


# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():

    return "My AI Backend is running!"


@app.route("/health")
def health():

    return {
        "status": "ok",
        "message": "Backend is working"
    }


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400

    user_message = data.get("message", "").strip()

    if not user_message:

        return jsonify({
            "error": "Message is required"
        }), 400

    try:

        # Save user message
        save_message("user", user_message)

        # Get previous conversation
        history = get_history()

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

        # Send conversation to Gemini
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents
        )

        ai_response = response.text

        # Save AI response
        save_message("model", ai_response)

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