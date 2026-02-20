# 🗄️ AI Database Console (React + Flask + LM Studio)

A local AI-powered **Database Console** that lets you ask natural language questions about your database and safely runs SQL queries for you.

This app runs **100% locally** using **LM Studio** (no OpenAI key, no cloud calls).

---

## ✨ Features

- 🧠 Local LLM via LM Studio (Qwen / Gemma, etc.)
- 🗄️ Natural language → SQL
- 🔒 Safe-by-default (read-only mode)
- ❌ Blocks destructive queries (DROP / ALTER / TRUNCATE)
- 📊 Clean, centered UI with table rendering
- 🔁 Session-based usage (per browser)
- ⚡ Fast local inference

---

## 🧩 Tech Stack

- **Frontend**: React (Vite)
- **Backend**: Flask (Python)
- **LLM Runtime**: LM Studio (OpenAI-compatible local API)
- **Database**: MySQL (can be adapted to Postgres)

---

## 📦 Project Structure

```txt
.
├── README.md
├── .gitignore
├── frontend/        # React UI (DB Console)
└── backend/       # Flask API
    ├── app.py
    ├── requirements.txt
```

## Test LM API Server
```bash
curl http://localhost:1234/v1/models
```

## Backend Setup (Flask API)
```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

## Frontend Setup (React UI)
```bash
cd frontend
npm install
npm run dev
```