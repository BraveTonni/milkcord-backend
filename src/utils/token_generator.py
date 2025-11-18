import secrets


def generate_access_token() -> str:
    return secrets.token_urlsafe(128)
