import json
import os
from flask import Blueprint, request, jsonify

theme_bp = Blueprint('theme', __name__)

_THEME_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'storage', 'theme.json'
)


def _load():
    try:
        with open(_THEME_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def _save(data):
    os.makedirs(os.path.dirname(_THEME_FILE), exist_ok=True)
    with open(_THEME_FILE, 'w') as f:
        json.dump(data, f)


@theme_bp.route('/api/theme', methods=['GET'])
def get_theme():
    data = _load()
    if data is None:
        return jsonify({'preset': 'warm'})
    return jsonify(data)


@theme_bp.route('/api/theme', methods=['POST'])
def set_theme():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'no data'}), 400
    _save(data)
    return jsonify({'ok': True})
