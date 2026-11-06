from app.services.user_service import get_user_by_login
from app.utils.hashing import verify_password
from app.utils.jwt import create_access_token
from app.schemas.auth import LoginRequest
from fastapi import HTTPException, status

async def authenticate_user(login_req: LoginRequest, require_admin: bool = False):
    user = await get_user_by_login(login_req.username)
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if require_admin and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    claims = {"sub": str(user._id), "username": user.username}
    if require_admin:
        claims["scope"] = "admin"
    token = create_access_token(claims)
    return token
