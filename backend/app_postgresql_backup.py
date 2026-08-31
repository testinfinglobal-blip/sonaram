import os
import base64
import uuid

import psycopg
from psycopg.rows import dict_row

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend")
)


# =========================================================
# FLASK
# =========================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from .env"
    )


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


# =========================================================
# OPENROUTER
# =========================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing from .env"
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


# =========================================================
# MODELS
# =========================================================

CHAT_MODEL = "openrouter/auto"

VISION_MODEL = "google/gemini-2.5-flash"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    try:

        connection = get_connection()

        connection.close()

        return jsonify({
            "status": "ok",
            "message": "Backend and PostgreSQL are working",
            "provider": "OpenRouter",
            "database": "PostgreSQL"
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": "Database connection failed",
            "details": str(error)
        }), 500


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name:

        return jsonify({
            "error": "Name is required"
        }), 400

    if not email:

        return jsonify({
            "error": "Email is required"
        }), 400

    if not password:

        return jsonify({
            "error": "Password is required"
        }), 400

    if len(password) < 6:

        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        # Check existing user

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            connection.close()

            return jsonify({
                "error": "Email already registered"
            }), 409


        # Hash password

        password_hash = generate_password_hash(
            password
        )


        # Create user

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, name, email, created_at
            """,
            (
                name,
                email,
                password_hash
            )
        )

        user = cursor.fetchone()

        connection.commit()

        connection.close()


        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": user
        }), 201


    except Exception as error:

        print("REGISTER ERROR:")
        print(error)

        return jsonify({
            "error": "Registration failed",
            "details": str(error)
        }), 500


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")


    if not email:

        return jsonify({
            "error": "Email is required"
        }), 400


    if not password:

        return jsonify({
            "error": "Password is required"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                created_at
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        connection.close()


        if not user:

            return jsonify({
                "error": "Invalid email or password"
            }), 401


        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return jsonify({
                "error": "Invalid email or password"
            }), 401


        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
        })


    except Exception as error:

        print("LOGIN ERROR:")
        print(error)

        return jsonify({
            "error": "Login failed",
            "details": str(error)
        }), 500


# =========================================================
# GET USER
# =========================================================

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        connection.close()


        if not user:

            return jsonify({
                "error": "User not found"
            }), 404


        return jsonify(user)


    except Exception as error:

        return jsonify({
            "error": "Failed to get user",
            "details": str(error)
        }), 500


# =========================================================
# CREATE NEW CHAT
# =========================================================

@app.route("/new-chat", methods=["POST"])
def new_chat():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400


    user_id = data.get("user_id")

    if not user_id:

        return jsonify({
            "error": "user_id is required"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        # Verify user

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if not user:

            connection.close()

            return jsonify({
                "error": "User not found"
            }), 404


        # Create chat

        chat_id = str(uuid.uuid4())


        cursor.execute(
            """
            INSERT INTO chats
            (id, user_id, title)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, title, created_at
            """,
            (
                chat_id,
                user_id,
                "New Chat"
            )
        )

        chat = cursor.fetchone()

        connection.commit()

        connection.close()


        return jsonify({
            "success": True,
            "chat": chat
        })


    except Exception as error:

        print("NEW CHAT ERROR:")
        print(error)

        return jsonify({
            "error": "Failed to create chat",
            "details": str(error)
        }), 500


# =========================================================
# GET USER CHATS
# =========================================================

@app.route("/chats", methods=["GET"])
def get_chats():

    user_id = request.args.get("user_id")


    if not user_id:

        return jsonify({
            "error": "user_id is required"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at
            FROM chats
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        chats = cursor.fetchall()

        connection.close()


        return jsonify(chats)


    except Exception as error:

        print("GET CHATS ERROR:")
        print(error)

        return jsonify({
            "error": "Failed to get chats",
            "details": str(error)
        }), 500


# =========================================================
# GET CHAT MESSAGES
# =========================================================

@app.route("/chats/<chat_id>/messages", methods=["GET"])
def get_messages(chat_id):

    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                role,
                message,
                created_at
            FROM messages
            WHERE chat_id = %s
            ORDER BY id ASC
            """,
            (chat_id,)
        )

        messages = cursor.fetchall()

        connection.close()


        return jsonify(messages)


    except Exception as error:

        print("GET MESSAGES ERROR:")
        print(error)

        return jsonify({
            "error": "Failed to get messages",
            "details": str(error)
        }), 500


# =========================================================
# SEND CHAT MESSAGE
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True)


    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400


    chat_id = data.get("chat_id")

    user_id = data.get("user_id")

    user_message = data.get(
        "message",
        ""
    ).strip()


    if not chat_id:

        return jsonify({
            "error": "chat_id is required"
        }), 400


    if not user_id:

        return jsonify({
            "error": "user_id is required"
        }), 400


    if not user_message:

        return jsonify({
            "error": "Message is required"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        # =================================================
        # CHECK CHAT BELONGS TO USER
        # =================================================

        cursor.execute(
            """
            SELECT id
            FROM chats
            WHERE id = %s
            AND user_id = %s
            """,
            (
                chat_id,
                user_id
            )
        )

        chat_exists = cursor.fetchone()


        if not chat_exists:

            connection.close()

            return jsonify({
                "error": "Chat not found for this user"
            }), 404


        # =================================================
        # SAVE USER MESSAGE
        # =================================================

        cursor.execute(
            """
            INSERT INTO messages
            (chat_id, role, message)
            VALUES (%s, %s, %s)
            """,
            (
                chat_id,
                "user",
                user_message
            )
        )

        connection.commit()


        # =================================================
        # GET HISTORY
        # =================================================

        cursor.execute(
            """
            SELECT
                role,
                message
            FROM messages
            WHERE chat_id = %s
            ORDER BY id ASC
            """,
            (chat_id,)
        )

        history = cursor.fetchall()

        connection.close()


        # =================================================
        # BUILD OPENROUTER MESSAGES
        # =================================================

        messages = []


        for row in history:

            role = row["role"]

            message = row["message"]


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


        print("=================================")
        print("SENDING TO OPENROUTER")
        print("MODEL:", CHAT_MODEL)
        print("MESSAGES:", len(messages))
        print("USER ID:", user_id)
        print("CHAT ID:", chat_id)
        print("=================================")


        # =================================================
        # OPENROUTER REQUEST
        # =================================================

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.7
        )


        if not response.choices:

            raise RuntimeError(
                "OpenRouter returned no choices"
            )


        ai_response = (
            response.choices[0]
            .message
            .content
        )


        if not ai_response:

            ai_response = (
                "AI response nahi mila."
            )


        print("AI RESPONSE:")
        print(ai_response)


        # =================================================
        # SAVE AI RESPONSE
        # =================================================

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            INSERT INTO messages
            (chat_id, role, message)
            VALUES (%s, %s, %s)
            """,
            (
                chat_id,
                "model",
                ai_response
            )
        )


        # =================================================
        # UPDATE CHAT TITLE
        # =================================================

        cursor.execute(
            """
            SELECT title
            FROM chats
            WHERE id = %s
            """,
            (chat_id,)
        )

        result = cursor.fetchone()


        if result:

            current_title = result["title"]


            if current_title == "New Chat":

                title = user_message[:100]


                cursor.execute(
                    """
                    UPDATE chats
                    SET title = %s
                    WHERE id = %s
                    """,
                    (
                        title,
                        chat_id
                    )
                )


        connection.commit()

        connection.close()


        return jsonify({
            "response": ai_response
        })


    except Exception as error:

        print("=================================")
        print("OPENROUTER ERROR")
        print(type(error).__name__)
        print(str(error))
        print("=================================")


        return jsonify({
            "error": "AI request failed",
            "details": str(error)
        }), 500


# =========================================================
# ANALYZE IMAGE
# =========================================================

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

        image_bytes = image.read()


        if not image_bytes:

            return jsonify({
                "error": "Uploaded image is empty"
            }), 400


        mime_type = (
            image.mimetype
            or "image/jpeg"
        )


        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        image_data_url = (
            f"data:{mime_type};base64,"
            f"{image_base64}"
        )


        # =================================================
        # VISION REQUEST
        # =================================================

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

                                "url":
                                    image_data_url
                            }

                        }

                    ]

                }

            ]

        )


        if not response.choices:

            raise RuntimeError(
                "Vision model returned no choices"
            )


        ai_response = (
            response.choices[0]
            .message
            .content
        )


        if not ai_response:

            ai_response = (
                "Image analysis response "
                "nahi mila."
            )


        return jsonify({
            "response": ai_response
        })


    except Exception as error:

        print("=================================")
        print("IMAGE ANALYSIS ERROR")
        print(type(error).__name__)
        print(str(error))
        print("=================================")


        return jsonify({
            "error": "Image analysis failed",
            "details": str(error)
        }), 500


# =========================================================
# RENAME CHAT
# =========================================================

@app.route(
    "/chats/<chat_id>/rename",
    methods=["PUT"]
)
def rename_chat(chat_id):

    data = request.get_json(silent=True)


    if not data:

        return jsonify({
            "error": "Request body is missing"
        }), 400


    new_title = data.get(
        "title",
        ""
    ).strip()


    user_id = data.get("user_id")


    if not user_id:

        return jsonify({
            "error": "user_id is required"
        }), 400


    if not new_title:

        return jsonify({
            "error": "Chat title is required"
        }), 400


    new_title = new_title[:100]


    try:

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT id
            FROM chats
            WHERE id = %s
            AND user_id = %s
            """,
            (
                chat_id,
                user_id
            )
        )


        if not cursor.fetchone():

            connection.close()

            return jsonify({
                "error": "Chat not found"
            }), 404


        cursor.execute(
            """
            UPDATE chats
            SET title = %s
            WHERE id = %s
            AND user_id = %s
            """,
            (
                new_title,
                chat_id,
                user_id
            )
        )


        connection.commit()

        connection.close()


        return jsonify({
            "success": True,
            "chat_id": chat_id,
            "title": new_title
        })


    except Exception as error:

        print("RENAME CHAT ERROR:")
        print(error)


        return jsonify({
            "error": "Failed to rename chat",
            "details": str(error)
        }), 500


# =========================================================
# DELETE CHAT
# =========================================================

@app.route(
    "/chats/<chat_id>",
    methods=["DELETE"]
)
def delete_chat(chat_id):

    data = request.get_json(
        silent=True
    ) or {}


    user_id = data.get("user_id")


    if not user_id:

        return jsonify({
            "error": "user_id is required"
        }), 400


    try:

        connection = get_connection()

        cursor = connection.cursor()


        # =================================================
        # CHECK CHAT
        # =================================================

        cursor.execute(
            """
            SELECT id
            FROM chats
            WHERE id = %s
            AND user_id = %s
            """,
            (
                chat_id,
                user_id
            )
        )


        if not cursor.fetchone():

            connection.close()

            return jsonify({
                "error": "Chat not found"
            }), 404


        # =================================================
        # DELETE MESSAGES
        # =================================================

        cursor.execute(
            """
            DELETE FROM messages
            WHERE chat_id = %s
            """,
            (chat_id,)
        )


        # =================================================
        # DELETE CHAT
        # =================================================

        cursor.execute(
            """
            DELETE FROM chats
            WHERE id = %s
            AND user_id = %s
            """,
            (
                chat_id,
                user_id
            )
        )


        connection.commit()

        connection.close()


        return jsonify({
            "success": True,
            "chat_id": chat_id
        })


    except Exception as error:

        print("DELETE CHAT ERROR:")
        print(error)


        return jsonify({
            "error": "Failed to delete chat",
            "details": str(error)
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )