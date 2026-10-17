import hashlib
import hmac
import secrets

_ITERATIONS = 260_000
_MIN_PASSWORD_LEN = 8


def validate_password_strength(password: str) -> str | None:
    if len(password) < _MIN_PASSWORD_LEN:
        return f"Password must be at least {_MIN_PASSWORD_LEN} characters"
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    )
    return f"pbkdf2_sha256${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rest = stored.split("$", 1)
        if algo != "pbkdf2_sha256":
            return False
        iterations_s, salt, expected_hex = rest.split("$", 2)
        iterations = int(iterations_s)
        if iterations < _ITERATIONS:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(digest.hex(), expected_hex)
    except (ValueError, TypeError):
        return False
