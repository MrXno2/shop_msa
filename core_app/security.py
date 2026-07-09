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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not autorization")
    try:
        payload = jwt.decode(access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalis token")


def set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.JWT_ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )