import hashlib
import hmac
import secrets

# OWASP: >= 600k итераций для PBKDF2-HMAC-SHA256 (2023); 390k — баланс
# скорости и безопасности для типовых паролей
_ITERATIONS = 390_000
_SALT_BYTES = 16
_ALGO = "pbkdf2_sha256"


def hash_password(raw_password: str) -> str:
    """Хэш пароля: pbkdf2_sha256$итерации$соль$дайджест.

    Соль уникальна для каждого пользователя, поэтому одинаковые пароли
    дают разные хэши. Старый unsalted sha256 больше не порождается.
    """
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return f"{_ALGO}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(raw_password: str, stored: str) -> bool:
    """Проверяет пароль по сохранённому хэшу.

    Понимает текущий формат pbkdf2 и legacy-формат unsalted sha256,
    чтобы старые аккаунты не разлогинивались после обновления.
    """
    if stored.startswith(f"{_ALGO}$"):
        try:
            _, iterations, salt, digest = stored.split("$")
        except ValueError:
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            raw_password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest)

    # Legacy: unsalted sha256
    legacy = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored)
