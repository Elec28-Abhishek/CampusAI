import os
from pathlib import Path


def _secret(name: str) -> str | None:
    try:
        import streamlit as st

        value = st.secrets.get(name)
        return str(value).strip() if value else None
    except Exception:
        return None


def _dotenv_value(name: str) -> str | None:
    """Read a simple KEY=value entry from the project's local .env file."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            key, separator, value = line.partition("=")
            if separator and key.strip() == name:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                return value.strip() or None
    except OSError:
        return None
    return None


def _configured_value(name: str) -> str | None:
    value = os.environ.get(name) or _secret(name) or _dotenv_value(name)
    return str(value).strip() if value and str(value).strip() else None


def google_maps_browser_key() -> str | None:
    """Load a browser-restricted Maps key from environment variables or secrets."""
    for name in ("GOOGLE_MAPS_BROWSER_API_KEY", "GOOGLE_MAPS_API_KEY"):
        value = _configured_value(name)
        if value:
            return value
    return None


def campus_admin_password() -> str | None:
    return _configured_value("CAMPUS_ADMIN_PASSWORD")


def campus_login_admin_password() -> str | None:
    """Optional password for creating the login-system administrator account."""
    return _configured_value("CAMPUS_LOGIN_ADMIN_PASSWORD")


def campus_login_admin_email() -> str:
    return _configured_value("CAMPUS_LOGIN_ADMIN_EMAIL") or "admin@campusai.com"
