import os
import re
import json
import time
import requests
import subprocess
import numpy as np
import pdfplumber

from flask import Flask, request, jsonify, send_from_directory
from flask_session import Session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# ==============================================================
# App Setup
# ==============================================================

app = Flask(__name__, static_folder="static", static_url_path="/")
app.secret_key = "oudience-fast-secret"

CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "flask_sessions"
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)

# ==============================================================
# Security
# ==============================================================

API_KEY = os.environ.get("OUDIENCE_API_KEY", "demo-key")

def check_api_key(req):
    return req.headers.get("x-api-key") == API_KEY

# ==============================================================
# Paths
# ==============================================================

KB_PATH = "knowledge_base.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==============================================================
# Ollama Detection
# ==============================================================

def ollama_available():
    try:
        subprocess.run(["ollama", "--version"], capture_output=True)
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

USE_OLLAMA = ollama_available()
print("Ollama detected:", USE_OLLAMA)

# ==============================================================
# Models
# ==============================================================

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

hf_generator = pipeline(
    "text-generation",
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    max_new_tokens=80,
    temperature=0.2,
    do_sample=False
)

# ==============================================================
# Knowledge Base
# ==============================================================

kb_docs = []
kb_embeddings = None

def load_knowledge_base():
    global kb_docs, kb_embeddings

    if not os.path.exists(KB_PATH) or os.path.getsize(KB_PATH) == 0:
        kb_docs, kb_embeddings = [], None
        return

    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb_docs = json.load(f)
    except json.JSONDecodeError:
        kb_docs, kb_embeddings = [], None
        return

    texts = [d["text"] for d in kb_docs if d.get("text")]
    if not texts:
        kb_embeddings = None
        return

    kb_embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

load_knowledge_base()

# ==============================================================
# Helpers
# ==============================================================

def chunk_text(text, size=300, overlap=40):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
    return chunks

def kb_search_multi(query, top_k=6, max_per_doc=2):
    if not kb_docs or kb_embeddings is None:
        return []

    q_emb = embedding_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    scores = np.dot(kb_embeddings, q_emb)
    ranked = np.argsort(scores)[::-1]

    results, seen = [], {}
    for idx in ranked:
        doc = kb_docs[idx]
        title = doc.get("title", "unknown")

        seen.setdefault(title, 0)
        if seen[title] >= max_per_doc:
            continue

        results.append(doc)
        seen[title] += 1
        if len(results) >= top_k:
            break

    return results

def quick_intent_reply(msg):
    m = msg.lower().strip()
    if m in {"hi", "hello", "hey"}:
        return "Hello! 👋 How can I help you today?"
    if m in {"how are you", "how r u", "how are u", "what's up", "whats up"}:
        return "I'm doing great! How can I assist you?"
    return None

def split_questions(prompt):
    text = prompt.replace("?", "?\n")
    parts = re.split(r"\n| and | & |,", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if len(p.strip()) > 4]

def clean_answer(text):
    if not text:
        return ""
    text = re.sub(r"\n{2,}", "\n", text)
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:3]).strip()

def build_prompt(question, context):
    return f"""
You are Oudience, a professional assistant.
Answer briefly and factually using only the context.

Context:
{context}

Question:
{question}

Answer:
"""

def generate_answer(prompt):
    start = time.time()

    if USE_OLLAMA:
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi", "prompt": prompt},
                stream=True,
                timeout=20
            )
            text = ""
            for line in r.iter_lines():
                if line and '"response":"' in line.decode("utf-8"):
                    text += line.decode("utf-8").split('"response":"')[1].split('"')[0]
            if text.strip():
                return text.strip(), time.time() - start
        except Exception:
            pass

    out = hf_generator(prompt)[0]["generated_text"]
    out = out.replace(prompt, "").strip()
    return out, time.time() - start

# ==============================================================
# API: Chat
# ==============================================================

@app.route("/query", methods=["POST"])
def query():
    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    user_prompt = data.get("query", "").strip()
    if not user_prompt:
        return jsonify({"error": "Empty message"}), 400

    quick = quick_intent_reply(user_prompt)
    if quick:
        return jsonify({"response": quick})

    questions = split_questions(user_prompt)
    if not questions:
        return jsonify({"response": "Please rephrase your question."})

    merged_answers = []

    for q in questions:
        docs = kb_search_multi(q)
        context = "\n".join(d["text"] for d in docs)
        prompt = build_prompt(q, context)
        raw, _ = generate_answer(prompt)
        merged_answers.append(clean_answer(raw))

    final_answer = " ".join(merged_answers)
    return jsonify({"response": final_answer})

# ==============================================================
# API: Admin Upload
# ==============================================================

@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"

    chunks = chunk_text(text)
    base_id = len(kb_docs)

    for i, c in enumerate(chunks):
        kb_docs.append({
            "id": base_id + i + 1,
            "title": filename,
            "text": c
        })

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb_docs, f, indent=2)

    load_knowledge_base()
    return jsonify({"chunks_added": len(chunks)})

# ==============================================================
# Static Routes
# ==============================================================

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/admin")
def admin():
    return send_from_directory("static", "admin.html")

# ==============================================================
# Run
# ==============================================================

if __name__ == "__main__":
    from waitress import serve
    print("🚀 Oudience Backend running on 0.0.0.0:5001")
    serve(app, host="0.0.0.0", port=5001)
