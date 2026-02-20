import os
import json
import re
from pathlib import Path
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from langchain_openai import ChatOpenAI
import pymysql

# -----------------------
# App Setup
# -----------------------
app = Flask(__name__)
CORS(app)

# -----------------------
# LLM Setup (LM Studio)
# -----------------------
LLM_MODEL = os.getenv("LM_MODEL", "qwen2.5-7b-instruct")
LLM_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")

llm_stream = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_base=LLM_BASE_URL,
    openai_api_key="lm-studio",
    temperature=0.7,
    streaming=True,
)

llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_base=LLM_BASE_URL,
    openai_api_key="lm-studio",
    temperature=0.7,
    streaming=False,
)

SYSTEM_PROMPT = "You are a helpful, concise assistant."

# -----------------------
# Persistence (Chat History)
# -----------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def load_history(session_id: str):
    file = DATA_DIR / f"{session_id}.json"
    if not file.exists():
        return []
    return json.loads(file.read_text())

def save_history(session_id: str, history: list):
    file = DATA_DIR / f"{session_id}.json"
    file.write_text(json.dumps(history, indent=2))

# -----------------------
# Database Helpers (MySQL)
# -----------------------
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USERNAME", "root"),
        password=os.getenv("DB_PASSWORD", "root@123"),
        database=os.getenv("DB_DATABASE", "laravel_test"),
        cursorclass=pymysql.cursors.Cursor,
    )

def get_db_schema(limit_tables=10, limit_cols=8):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = cur.fetchall()[:limit_tables]

    schema = []
    for (table,) in tables:
        cur.execute(f"DESCRIBE `{table}`")
        cols = cur.fetchall()[:limit_cols]
        col_names = ", ".join([c[0] for c in cols])
        schema.append(f"{table}({col_names})")

    conn.close()
    return "\n".join(schema)

def clean_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```sql", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    text = re.sub(r"^sql\s*:\s*", "", text, flags=re.IGNORECASE).strip()
    return text.rstrip(";").strip()

# -----------------------
# Chat Endpoint (Streaming + Sessions + Persistence)
# -----------------------
@app.route("/api/chat/<session_id>", methods=["POST"])
def chat(session_id):
    data = request.json
    message = data.get("message", "")

    history = load_history(session_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    def stream():
        full_reply = ""
        for chunk in llm_stream.stream(messages):
            token = chunk.content or ""
            full_reply += token
            yield f"data: {token}\n\n"

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": full_reply})
        save_history(session_id, history)

    return Response(stream(), mimetype="text/event-stream")

@app.route("/api/history/<session_id>", methods=["GET"])
def get_history(session_id):
    return jsonify(load_history(session_id))

# -----------------------
# Database Console Endpoint
# -----------------------
@app.route("/api/db/<session_id>", methods=["POST"])
def db_console(session_id):
    data = request.json
    question = data.get("question", "")
    allow_write = bool(data.get("allow_write", False))

    schema = get_db_schema()

    rules = """
Allowed SQL:
- SELECT only.
""" if not allow_write else """
Allowed SQL:
- SELECT
- INSERT
- UPDATE
- DELETE

Rules:
- NEVER use DROP, ALTER, TRUNCATE.
- UPDATE/DELETE must include WHERE.
"""

    prompt = f"""
You are a MySQL expert.

Database schema:
{schema}

User question:
{question}

{rules}

Return only plain SQL. No markdown, no explanation.
"""

    raw = llm.invoke(prompt).content
    sql = clean_sql(raw)
    sql_lc = sql.lower().lstrip()

    forbidden = ["drop", "alter", "truncate"]
    if any(word in sql_lc for word in forbidden):
        return jsonify({"error": "Forbidden SQL", "sql": sql}), 400

    if not allow_write and not sql_lc.startswith("select"):
        return jsonify({"error": "Only SELECT allowed", "sql": sql}), 400

    if allow_write and sql_lc.startswith(("update", "delete")) and " where " not in sql_lc:
        return jsonify({"error": "UPDATE/DELETE must include WHERE", "sql": sql}), 400

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql)

        if sql_lc.startswith("select"):
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            result = {"columns": cols, "rows": rows}
        else:
            conn.commit()
            result = {"affected_rows": cur.rowcount}

        conn.close()
        return jsonify({"sql": sql, **result})

    except Exception as e:
        return jsonify({"error": str(e), "sql": sql}), 500

# -----------------------
# Health Check
# -----------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)