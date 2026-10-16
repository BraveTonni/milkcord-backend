import hashlib

from src.utils.crypto import hash_password, verify_password


def test_hash_is_salted_pbkdf2():
    first = hash_password("secret")
    second = hash_password("secret")

    assert first.startswith("pbkdf2_sha256$")
    assert first != second  # у каждого хэша своя соль
    assert verify_password("secret", first)


def test_wrong_password_rejected():
    stored = hash_password("secret")

    assert not verify_password("other-password", stored)


def test_legacy_unsalted_sha256_still_accepted():
    legacy = hashlib.sha256(b"secret").hexdigest()

    assert verify_password("secret", legacy)
    assert not verify_password("other-password", legacy)


def test_malformed_hash_rejected():
    assert not verify_password("secret", "pbkdf2_sha256$not-a-valid-hash")
