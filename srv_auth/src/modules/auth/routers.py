from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
import jwt
from core_app.security import create_access_token, set_access_cookie, is_validity_token


router = APIRouter(prefix="/auth")


@router.post("/login")
async def auth_login_user(response: Response):
    token = create_access_token({"sub": "user_id_123"})
    set_access_cookie(response, token)
    return {"message": "logged in"}


@router.post("/register")
async def auth_register_user():
    ...

@router.get("/me")
async def me_user(payload = Depends(is_validity_token)):
    return payload


