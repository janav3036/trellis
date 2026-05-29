import json 
import requests as req
from flask import Blueprint, Response, request, jsonify, session, stream_with_context
from noterag import retriever, indexer, store
from noterag.chat import stream_chat
from storage.db import get_config, get_connection, set_config

noterag_bp = Blueprint("noterag", __name__)

@noterag_bp.before_request
def require_auth():
    if not session.get("authed"):
        return jsonify({"error": "unauthorized"}), 401

# -- Chat ----------    
@noterag_bp.route("/chat", methods=["POST"])
def chat():
    body = request.json or {}
    query = (body.get("query") or "").strip()
    history = body.get("history", [])[-10:]
    profile = get_config("noterag_profile") or ""
    custom_prompt = get_config("noterag_custom_prompt") or ""

    if not query:
        return jsonify({"error": "query required"}), 400

    chunks = retriever.retrieve(query, n=8)

    def generate():
        yield f"SOURCES:{json.dumps([c['metadata'] for c in chunks])}\n"
        for token in stream_chat(query, chunks, history, profile, custom_prompt):
            yield token
    
    return Response(
        stream_with_context(generate()),
        content_type="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )

#-- Sessions ------

@noterag_bp.route("/sessions", methods=["GET"])
def list_sessions():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@noterag_bp.route("/sessions", methods=["POST"])
def create_session():
    title = (request.json or {}).get("title", "New Chat")
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute(
            "INSERT INTO chat_sessions (title) VALUES (?)", (title,)
        )
        session_id = cur.lastrowid
    return jsonify({"id": session_id, "title": title})

@noterag_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        s = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions where id = ?",
            (session_id,)
        ).fetchone()
        if not s:
            return jsonify({"error": "not found"}), 404
        msgs = conn.execute(
            "SELECT role, text, sources FROM chat_messages WHERE session_id = ? ORDER BY created_at",
            (session_id,)
        ).fetchall()
    
    return jsonify({
        **dict(s),
        "messages": [
            {"role": m["role"], "text": m["text"], "sources": json.loads(m["sources"])} for m in msgs
        ],
    })

@noterag_bp.route("/sessions/<int:session_id>", methods=["PATCH"])
def update_session(session_id):
    title = (request.json or {}).get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, session_id)
        )
    return jsonify({"ok": True})

@noterag_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    return jsonify({"ok": True})

@noterag_bp.route("/sessions/<int:session_id>/messages", methods=["POST"])
def save_messages(session_id):
    messages = request.json or []
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for msg in messages:
            conn.execute(
                "INSERT INTO chat_messages (session_id, role, text, sources) VALUES (?, ?, ?, ?)", 
                (session_id, msg["role"], msg["text"], json.dumps(msg.get("sources", [])))
            )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,) 
        )
    return jsonify({"ok": True})

# -- Profile -----
@noterag_bp.route("/profile", methods=["GET"])
def get_profile():
    return jsonify({"profile": get_config("noterag_profile") or ""})


@noterag_bp.route("/profile", methods=["POST"])
def save_profile():
    text = (request.json or {}).get("profile", "").strip()
    set_config("noterag_profile", text)
    return jsonify({"ok": True})


@noterag_bp.route("/profile/generate", methods=["POST"])
def generate_profile():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT source, event_type, metadata, timestamp FROM events ORDER BY timestamp DESC LIMIT 120",

        ).fetchall()
    lines = []
    for row in rows:
        try:
            meta = json.loads(row["metadata"])
            date = row["timestamp"][:10]
            src = row["source"]
            if src == "spotify":
                lines.append(f"Listened to {meta.get('track_name','')} by {meta.get('artist','')} on {date}")
            elif src == "github":
                lines.append(f"Committed: {meta.get('message','')} in {meta.get('repo','')} on {date}")
            elif src == "dreams":
                lines.append(f"Dream on {date}: {meta.get('title','')} — {meta.get('description','')[:120]}")
            elif src == "movies":
                lines.append(f"Watched {meta.get('title','')} on {date}")
            elif src == "people":
                lines.append(f"Met {meta.get('name','')} on {date}")
            elif src == "quotes":
                lines.append(f"Saved quote: \"{meta.get('text','')}\" on {date}")
            elif src == "habits":
                lines.append(f"Completed habit '{meta.get('habit_name','')}' on {date}")
        except Exception:
            pass

    activity = "\n".join(lines[:80])
    prompt = (
        "Based on these personal logs, write a warm, specific 2-3 paragraph profile of this person. "
        "Focus on their interests, habits, creative patterns, and personality. "
        "Be personal and specific, not generic.\n\n"
        f"Recent activity:\n{activity}\n\nProfile:"
    )

    resp = req.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
        timeout=120,

    )
    profile_text = resp.json().get("response", "").strip()
    set_config("noterag_profile", profile_text)
    return jsonify({"profile": profile_text})

# -- Custom prompt --------

@noterag_bp.route("/custom-prompt", methods=["GET"])
def get_custom_prompt():
    return jsonify({"custom_prompt": get_config("noterag_custom_prompt") or ""})

@noterag_bp.route("/custom-prompt", methods=["POST"])
def save_custom_prompt():
    text = (request.json or {}).get("custom_prompt", "").strip()
    set_config("noterag_custom_prompt", text)
    return jsonify({"ok": True})

# -- Index / Status -------

@noterag_bp.route("/index", methods=["POST"])
def run_index():
    count = indexer.index_events()
    return jsonify({"indexed": count})

@noterag_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"total_chunks": store.count()})