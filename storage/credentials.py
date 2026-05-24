"""
Credential resolution: environment variable first, macOS keyring as fallback
(so local dev continues to work without any changes).
"""
import os


def get(env_var: str, keyring_service: str, keyring_key: str) -> str | None:
    val = os.environ.get(env_var)
    if val:
        return val
    try:
        import keyring as _kr
        return _kr.get_password(keyring_service, keyring_key)
    except Exception:
        return None
