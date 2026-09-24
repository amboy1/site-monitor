from datetime import datetime, timedelta, timezone
import jwt

SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_ME_LATER"  # В реальном проекте вынесем в .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Декодирует токен и возвращает его содержимое (payload).
    
    Может выбрасывать:
    - jwt.ExpiredSignatureError: если срок действия токена истек
    - jwt.InvalidTokenError: если токен невалиден
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
