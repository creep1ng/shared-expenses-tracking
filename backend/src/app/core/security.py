from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from app.core.config import Settings

PBKDF2_ITERATIONS = 600_000


@dataclass(frozen=True)
class PasswordHash:
    value: str


def hash_password(password: str, settings: Settings) -> PasswordHash:
    salt = secrets.token_bytes(16)
    pepper = settings.auth_password_pepper.get_secret_value().encode("utf-8")
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8") + pepper, salt, PBKDF2_ITERATIONS
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return PasswordHash(value=f"pbkdf2_sha256${PBKDF2_ITERATIONS}${encoded_salt}${encoded_digest}")


def verify_password(password: str, password_hash: str, settings: Settings) -> bool:
    try:
        algorithm, iterations_raw, encoded_salt, encoded_digest = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    iterations = int(iterations_raw)
    salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
    expected_digest = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
    pepper = settings.auth_password_pepper.get_secret_value().encode("utf-8")
    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8") + pepper,
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def generate_urlsafe_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_reset_token(token: str, settings: Settings) -> str:
    pepper = settings.auth_reset_token_pepper.get_secret_value()
    return hashlib.sha256(f"{pepper}:{token}".encode()).hexdigest()
