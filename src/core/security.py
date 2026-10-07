import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt

# Secret key a tokenek aláírásához
SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 hét


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Ellenőrzi a jelszót a közvetlen bcrypt használatával."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Legenerálja a jelszó bcrypt hash-ét (max 72 bájt)."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """JWT Access Token kiállítása."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt