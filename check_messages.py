import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

chat_id = "6a8a4e31-5d87-4325-a8fb-f71a96d8b31e"

conn = psycopg.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    SELECT id, chat_id, role, message, created_at
    FROM messages
    WHERE chat_id = %s
    ORDER BY id ASC
""", (chat_id,))

rows = cur.fetchall()

print("\n===== MESSAGES =====")

for row in rows:
    print(row)

print("====================")

cur.close()
conn.close()