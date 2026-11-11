"""Password hashing helpers for CampusAI's demonstration account system."""

from __future__ import annotations

import hashlib
import hmac
import secrets


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(stored_value: str, supplied_password: str) -> bool:
    """Verify new hashes and permit migration of old local plaintext rows."""
    try:
        algorithm, iterations, salt_hex, expected_hex = stored_value.split("$", 3)
        if algorithm != _ALGORITHM:
            raise ValueError("Unsupported password format")
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            supplied_password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), expected_hex)
    except (ValueError, TypeError):
        # Existing local databases may have plaintext rows. Successful logins
        # are re-hashed by the login page; new registrations are never plain text.
        return hmac.compare_digest(stored_value, supplied_password)


def is_password_hash(value: str) -> bool:
    return value.startswith(f"{_ALGORITHM}$")
