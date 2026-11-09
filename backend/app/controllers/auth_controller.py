from fastapi import APIRouter
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user
from app.core.config import ENABLE_ADMIN

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(login_req: LoginRequest):
    token = await authenticate_user(login_req)
    return TokenResponse(access_token=token)


if ENABLE_ADMIN:
    @router.post("/admin/login", response_model=TokenResponse)
    async def admin_login(login_req: LoginRequest):
        token = await authenticate_user(login_req, require_admin=True)
        return TokenResponse(access_token=token)
