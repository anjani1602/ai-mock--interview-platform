import os
import sqlite3
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify
from flask_cors import CORS


# =========================
# Load .env file
# =========================

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            os.environ.setdefault(
                key.strip(),
                value.strip().strip('"').strip("'")
            )


load_env()


# =========================
# Configuration
# =========================

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
PORT = int(os.environ.get("PORT", "8000"))

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "interviews.db"
)


# =========================
# Flask
# =========================

app = Flask(__name__)
CORS(app)


# =========================
# Database
# =========================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                feedback TEXT,
                score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


# =========================
# Gemini API
# =========================

def ask_gemini(prompt):
    if not API_KEY:
        raise Exception(
            "GEMINI_API_KEY is missing. "
            "Please add it to the .env file."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + MODEL
        + ":generateContent?key="
        + API_KEY
    )

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        raise Exception(
            f"Gemini API error {error.code}: {error_body}"
        )

    except Exception as error:
        raise Exception(
            f"Gemini request failed: {error}"
        )


# =========================
# Home / Health check
# =========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AI Mock Interview backend is running",
        "status": "success",
        "model": MODEL
    })


# =========================
# Start Interview
# =========================

@app.route("/api/start", methods=["POST"])
def start_interview():

    try:
        data = request.get_json() or {}

        topic = data.get("topic", "Python")

        prompt = f"""
You are an AI mock interview interviewer.

The interview topic is: {topic}

Generate ONE interview question about {topic}.

Rules:
- Ask only one question.
- Do not give the answer.
- The question should be suitable for a student/job interview.
- Return only the question.
"""

        question = ask_gemini(prompt)

        return jsonify({
            "success": True,
            "topic": topic,
            "question": question.strip()
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================
# Submit Answer
# =========================

@app.route("/api/answer", methods=["POST"])
def submit_answer():

    try:
        data = request.get_json() or {}

        topic = data.get("topic", "Python")
        question = data.get("question", "")
        answer = data.get("answer", "")

        if not question:
            return jsonify({
                "success": False,
                "error": "Question is required"
            }), 400

        if not answer:
            return jsonify({
                "success": False,
                "error": "Answer is required"
            }), 400

        prompt = f"""
You are an AI interview evaluator.

Topic:
{topic}

Interview Question:
{question}

Candidate Answer:
{answer}

Evaluate the candidate's answer.

Give:
1. Score out of 10
2. What was done well
3. What could be improved
4. A better sample answer

Keep the feedback clear and suitable for a student.

At the end, write:

SCORE: X/10
"""

        feedback = ask_gemini(prompt)

        score = 0

        # Try to find score from Gemini response
        import re

        match = re.search(
            r"SCORE:\s*(\d+)",
            feedback,
            re.IGNORECASE
        )

        if match:
            score = int(match.group(1))
            score = max(0, min(score, 10))

        # Save interview to database
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO interviews
                (topic, question, answer, feedback, score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                topic,
                question,
                answer,
                feedback,
                score
            ))

            interview_id = cursor.lastrowid
            conn.commit()

        return jsonify({
            "success": True,
            "id": interview_id,
            "score": score,
            "feedback": feedback
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================
# Interview History
# =========================

@app.route("/api/history", methods=["GET"])
def history():

    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT
                    id,
                    topic,
                    question,
                    answer,
                    feedback,
                    score,
                    created_at
                FROM interviews
                ORDER BY id DESC
            """).fetchall()

        interviews = []

        for row in rows:
            interviews.append({
                "id": row["id"],
                "topic": row["topic"],
                "question": row["question"],
                "answer": row["answer"],
                "feedback": row["feedback"],
                "score": row["score"],
                "created_at": row["created_at"]
            })

        return jsonify({
            "success": True,
            "history": interviews
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================
# Run Server
# =========================

if __name__ == "__main__":

    init_db()

    if API_KEY:
        print("Gemini API key loaded successfully.")
    else:
        print("WARNING: GEMINI_API_KEY not found.")

    print(f"Gemini model: {MODEL}")
    print(f"Mock Interview running at http://localhost:{PORT}")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    )