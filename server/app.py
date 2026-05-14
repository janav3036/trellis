import socket
from flask import Flask
from server.routes.api import api_bp

# macOS: Python's getaddrinfo can fail for hostnames that curl resolves fine.
# Force IPv4 to match curl's default behaviour.
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, typ=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, typ, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)