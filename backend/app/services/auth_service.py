from app.services.user_service import get_user_by_username
from app.utils.hashing import verify_password
from app.utils.jwt import create_access_token
from app.schemas.auth import LoginRequest
from fastapi import HTTPException, status

async def authenticate_user(login_req: LoginRequest):
    user = await get_user_by_username(login_req.username)
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user._id), "username": user.username})
    return token 