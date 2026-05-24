import os
import secrets
import socket
import keyring
from flask import Flask
from server.routes.api import api_bp

_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, typ=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, typ, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

def _get_secret_key():
    key = os.environ.get("FLASK_SECRET_KEY") or keyring.get_password("trellis", "flask_secret_key")
    if not key:
        key = secrets.token_hex(32)
        keyring.set_password("trellis", "flask_secret_key", key)
    return key

def create_app():
    app = Flask(__name__)
    app.secret_key = _get_secret_key()
    app.config["SESSION_PERMANENT"] = False
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)