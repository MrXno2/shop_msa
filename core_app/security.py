from datetime import datetime, timedelta, timezone
from fastapi import Cookie, HTTPException, Response, status
import jwt
from core_app.settings import settings


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES_SECONDS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def is_validity_token(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        payload = jwt.decode(access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def is_admin_token(admin_access_token: str = Cookie(None)):
    payload = is_validity_token(admin_access_token)
    if payload.get("uuid") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not admin")
    return payload



def set_cookie(name_token: str, response: Response, token: str) -> None:
    response.set_cookie(
        key=name_token,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",  # 👈 Или "none"
        domain="127.0.0.1",  # 👈 Добавь явно домен
        path="/",  # 👈 Чтобы кука была доступна на всех путях
    )
