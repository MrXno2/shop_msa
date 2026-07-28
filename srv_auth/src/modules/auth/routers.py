from fastapi import APIRouter, Depends, Response, status

import core_app.security as security
from srv_auth.src.dependensies import AuthServiceDep
from srv_auth.src.modules.auth.schemas import AuthLoginAdminReqSchema, AuthLoginReqSchema, AuthRegisterReqSchema

router = APIRouter(prefix="/auth")


@router.post("/login", status_code=status.HTTP_200_OK)
async def auth_login_user(req_data: AuthLoginReqSchema, response: Response, auth_service: AuthServiceDep) -> None:
    uuid_user = await auth_service.login_user(req_data)
    token = security.create_access_token({"uuid": uuid_user})
    security.set_cookie("access_token", response, token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def auth_register_user(req_data: AuthRegisterReqSchema, auth_service: AuthServiceDep, response: Response):
    uuid_user = await auth_service.register_user(req_data)
    token = security.create_access_token({"uuid": uuid_user})
    security.set_cookie("access_token", response, token)
    return token


@router.post("/login_admin", status_code=status.HTTP_200_OK)
async def auth_login_admin(req_data: AuthLoginAdminReqSchema, response: Response, auth_service: AuthServiceDep) -> None:
    await auth_service.login_admin(req_data)
    token = security.create_access_token({"uuid": "admin"})
    security.set_cookie("admin_access_token", response, token)


@router.get("/me")
async def me_user(payload=Depends(security.is_validity_token)):
    return payload.get("uuid")


@router.get("/me_admin")
async def me_admin(payload=Depends(security.is_admin_token)):
    return payload.get("uuid")
