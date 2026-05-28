import os
import secrets
import socket
from flask import Flask, send_from_directory
from server.routes.api import api_bp
from server.routes.noterag import noterag_bp
from server.routes.chatstats import chatstats_bp
from server.routes.theme import theme_bp
from storage.db import apply_schema

_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, typ=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, typ, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

_FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist'))

_SECRET_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'storage', '.secret_key')

def _get_secret_key():
    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key
    try:
        with open(_SECRET_KEY_FILE) as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    key = secrets.token_hex(32)
    with open(_SECRET_KEY_FILE, 'w') as f:
        f.write(key)
    return key

def create_app():
    apply_schema()
    app = Flask(__name__, static_folder=None)
    app.secret_key = _get_secret_key()
    app.config["SESSION_PERMANENT"] = False
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(noterag_bp, url_prefix="/api/noterag")
    app.register_blueprint(theme_bp)
    app.register_blueprint(chatstats_bp, url_prefix="/api/chats")

    @app.route("/health")
    def health():
        from flask import jsonify
        index = os.path.join(_FRONTEND_DIST, "index.html")
        return jsonify(dist=_FRONTEND_DIST, index_exists=os.path.isfile(index))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        full = os.path.join(_FRONTEND_DIST, path)
        if path and os.path.isfile(full):
            return send_from_directory(_FRONTEND_DIST, path)
        return send_from_directory(_FRONTEND_DIST, "index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False, port=5000)
