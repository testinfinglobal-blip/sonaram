import os
import sqlite3
import uuid
import base64

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI


# =========================================
# LOAD ENVIRONMENT
# =========================================

load_dotenv()
app = Flask(__name__, static_folder="../frontend", static_url_path="")

CORS(app)


# =========================================
# OPENROUTER
# =========================================

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing from .env"
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# =========================================
# MODEL
# =========================================

CHAT_MODEL = "openrouter/auto"

# Vision model
VISION_MODEL = "google/gemini-2.5-flash"


# =========================================
# DATABASE
# =========================================

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


# =========================================
# HOME
# =========================================
@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")

# =========================================
# HEALTH
# =========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "message": "Backend is working",
        "provider": "OpenRouter"
    })


# =========================================
# CREATE NEW CHAT
# =========================================

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


# =========================================
# GET CHAT HISTORY
# =========================================

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


# =========================================
# GET MESSAGES
# =========================================

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


# =========================================
# SEND CHAT MESSAGE
# =========================================

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

        # ---------------------------------
        # CHECK CHAT
        # ---------------------------------

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


        # ---------------------------------
        # SAVE USER MESSAGE
        # ---------------------------------

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


        # ---------------------------------
        # GET HISTORY
        # ---------------------------------

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


        # ---------------------------------
        # BUILD OPENROUTER MESSAGES
        # ---------------------------------

        messages = []

        for role, message in history:

            if role == "user":

                messages.append({
                    "role": "user",
                    "content": message
                })

            elif role == "model":

                messages.append({
                    "role": "assistant",
                    "content": message
                })


        # ---------------------------------
        # OPENROUTER REQUEST
        # ---------------------------------

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages
        )


        ai_response = (
            response.choices[0].message.content
            or "AI response nahi mila."
        )


        # ---------------------------------
        # SAVE AI RESPONSE
        # ---------------------------------

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


        # ---------------------------------
        # CREATE CHAT TITLE
        # ---------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT title FROM chats WHERE id = ?",
            (chat_id,)
        )

        result = cursor.fetchone()

        if result:

            current_title = result[0]

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

        print("OPENROUTER ERROR:")
        print(error)

        return jsonify({
            "error": "AI request failed",
            "details": str(error)
        }), 500


# =========================================
# ANALYZE UPLOADED IMAGE
# =========================================

@app.route("/analyze-image", methods=["POST"])
def analyze_image():

    if "image" not in request.files:

        return jsonify({
            "error": "Image is required"
        }), 400


    image = request.files["image"]


    if image.filename == "":

        return jsonify({
            "error": "No image selected"
        }), 400


    try:

        # ---------------------------------
        # READ IMAGE
        # ---------------------------------

        image_bytes = image.read()


        if not image_bytes:

            return jsonify({
                "error": "Uploaded image is empty"
            }), 400


        # ---------------------------------
        # MIME TYPE
        # ---------------------------------

        mime_type = image.mimetype or "image/jpeg"


        # ---------------------------------
        # BASE64 IMAGE
        # ---------------------------------

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        image_data_url = (
            f"data:{mime_type};base64,{image_base64}"
        )


        # ---------------------------------
        # OPENROUTER VISION REQUEST
        # ---------------------------------

        response = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",

                            "text":
                                "Analyze this image and "
                                "describe what you see clearly."
                        },

                        {
                            "type": "image_url",

                            "image_url": {
                                "url": image_data_url
                            }
                        }

                    ]
                }

            ]
        )


        ai_response = (
            response.choices[0].message.content
            or "Image analysis response nahi mila."
        )


        return jsonify({
            "response": ai_response
        })


    except Exception as error:

        print("IMAGE ANALYSIS ERROR:")
        print(error)

        return jsonify({
            "error": "Image analysis failed",
            "details": str(error)
        }), 500


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

 # =========================================
# RENAME CHAT
# =========================================

@app.route("/chats/<chat_id>/rename", methods=["PUT"])
def rename_chat(chat_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is missing"
        }), 400

    new_title = data.get("title", "").strip()

    if not new_title:
        return jsonify({
            "error": "Chat title is required"
        }), 400

    new_title = new_title[:100]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM chats WHERE id = ?",
        (chat_id,)
    )

    if not cursor.fetchone():
        connection.close()

        return jsonify({
            "error": "Chat not found"
        }), 404

    cursor.execute(
        """
        UPDATE chats
        SET title = ?
        WHERE id = ?
        """,
        (new_title, chat_id)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "chat_id": chat_id,
        "title": new_title
    })


# =========================================
# DELETE CHAT
# =========================================

@app.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM chats WHERE id = ?",
        (chat_id,)
    )

    if not cursor.fetchone():
        connection.close()

        return jsonify({
            "error": "Chat not found"
        }), 404

    cursor.execute(
        "DELETE FROM messages WHERE chat_id = ?",
        (chat_id,)
    )

    cursor.execute(
        "DELETE FROM chats WHERE id = ?",
        (chat_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "chat_id": chat_id
    })


# =========================================
# RUN SERVER
# =========================================

# local run
# if __name__ == "__main__":
#     app.run(
#         host="127.0.0.1",
#         port=5000,
#         debug=True
#     )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )