import secrets
import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
PASSWORD_ALPHABET = string.ascii_letters + string.digits
DEFAULT_PASSWORD_LENGTH = 12


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password() -> str:
    while True:
        password = "".join(
            secrets.choice(PASSWORD_ALPHABET) for _ in range(DEFAULT_PASSWORD_LENGTH)
        )
        if any(char.isalpha() for char in password) and any(
            char.isdigit() for char in password
        ):
            return password
