import os
import secrets
import socket
from flask import Flask, send_from_directory
from server.routes.api import api_bp
from server.routes.noterag import noterag_bp
from storage.credentials import get as get_cred
from storage.db import apply_schema

_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, typ=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, typ, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

_FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist'))

def _get_secret_key():
    key = get_cred("FLASK_SECRET_KEY", "trellis", "flask_secret_key")
    if not key:
        key = secrets.token_hex(32)
        try:
            import keyring
            keyring.set_password("trellis", "flask_secret_key", key)
        except Exception:
            pass
    return key

def create_app():
    apply_schema()
    app = Flask(__name__, static_folder=None)
    app.secret_key = _get_secret_key()
    app.config["SESSION_PERMANENT"] = False
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(noterag_bp, url_prefix="/api/noterag")

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
    app.run(debug=True, port=5000)
