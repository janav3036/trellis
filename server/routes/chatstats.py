import json
import os
import tempfile
from flask import Blueprint, jsonify, request, Response, session
from werkzeug.utils import secure_filename
from storage.db import get_connection
from ingesters.whatsapp import parse as wa_parse
from surfaces.chat_stats import compute_stats, generate_report

chatstats_bp = Blueprint('chatstats', __name__)

_AUTH_FREE = set()

@chatstats_bp.before_request
def require_auth():
    if not session.get('authed'):
        return jsonify({"error": "unauthorized"}), 401
    
@chatstats_bp.route('/upload', methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files['file']
    chat_name = request.form.get('chat_name', '').strip()
    if not chat_name:
        chat_name = secure_filename(f.filename).replace('.txt', '').replace('_', ' ')

    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        messages = wa_parse(tmp_path, chat_name)
    finally:
        os.unlink(tmp_path)

    if not messages:
        return jsonify({'error': 'no messages parsed - check file format'}), 422
    
    participants = sorted({m['sender'] for m in messages})
    date_from = min(m['timestamp'] for m in messages).isoformat()
    date_to = max(m['timestamp'] for m in messages).isoformat()

    with get_connection() as conn:
        conn.execute('DELETE FROM whatsapp_messages WHERE chat_name = ?', (chat_name,))
        conn.execute(
            '''INSERT OR REPLACE INTO whatsapp_chats
               (chat_name, file_name, message_count, participants, date_from, date_to)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (chat_name, secure_filename(f.filename), len(messages),
             json.dumps(participants), date_from, date_to)
        )
        conn.executemany(
            'INSERT INTO whatsapp_messages (chat_name, timestamp, sender, message) VALUES (?,?,?,?)',
            [(chat_name, m['timestamp'].isoformat(), m['sender'], m['message']) for m in messages]
        )

    return jsonify({"ok": True, 'chat_name': chat_name, 'message_count': len(messages), 'participants': participants})
    
@chatstats_bp.route('/', methods=["GET"])
def list_chats():
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT chat_name, file_name, message_count, participants, date_from, date_to, ingested_at FROM whatsapp_chats ORDER BY ingested_at DESC'
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@chatstats_bp.route('/<chat_name>/report', methods=["GET"])
def report(chat_name):
    stats = compute_stats(chat_name)
    if not stats:
        return jsonify({"error": "chat not found or empty"}), 404
    html = generate_report(stats)
    return Response(html, mimetype='text/html')

@chatstats_bp.route('/<chat_name>', methods=["DELETE"])
def delete_chat(chat_name):
    with get_connection() as conn:
        conn.execute('DELETE FROM whatsapp_chats WHERE chat_name = ?', (chat_name,))
    return jsonify({'ok': True})