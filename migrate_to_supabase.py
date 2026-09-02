import sqlite3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# -----------------------------
# SUPABASE CONNECTION
# -----------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL or SUPABASE_KEY is missing from .env")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# -----------------------------
# READ LOCAL SQLITE DATABASE
# -----------------------------

DATABASE = "feedback.db"

connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row

rows = connection.execute("""
    SELECT
        id,
        student_name,
        school_id,
        class_name,
        section,
        feedback_type,
        subject,
        problems,
        rating,
        additional_feedback,
        status,
        created_at
    FROM feedback
    ORDER BY id
""").fetchall()

connection.close()

print(f"Found {len(rows)} feedback records in SQLite.")

# -----------------------------
# PREPARE DATA
# -----------------------------

records = []

for row in rows:

    record = {
        "id": row["id"],
        "student_name": row["student_name"],
        "school_id": row["school_id"],
        "class_name": row["class_name"],
        "section": row["section"],
        "feedback_type": row["feedback_type"],
        "subject": row["subject"],
        "problems": row["problems"],
        "rating": row["rating"],
        "additional_feedback": row["additional_feedback"],
        "status": row["status"] or "New",
        "created_at": row["created_at"]
    }

    records.append(record)

# -----------------------------
# UPLOAD TO SUPABASE
# -----------------------------

if not records:

    print("No records found. Nothing to migrate.")

else:

    response = supabase \
        .table("feedback") \
        .insert(records) \
        .execute()

    print("Migration completed successfully.")

    print(f"Uploaded {len(records)} records.")