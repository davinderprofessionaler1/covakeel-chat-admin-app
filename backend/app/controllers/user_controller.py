from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import get_current_user
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    existing = await user_service.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = await user_service.create_user(user)
    created = await user_service.get_user_by_id(user_id)
    return UserRead(
        id=str(created._id),
        username=created.username,
        email=created.email,
        createdAt=created.createdAt
    )


@router.get("/me", response_model=UserRead)
async def register(user=Depends(get_current_user)):
    return UserRead(
        id=str(user._id),
        username=user.username,
        email=user.email,
        createdAt=user.createdAt
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(
        id=str(user._id),
        username=user.username,
        email=user.email,
        createdAt=user.createdAt
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, user_update: UserUpdate):
    updated = await user_service.update_user(user_id, user_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(
        id=str(updated._id),
        username=updated.username,
        email=updated.email,
        createdAt=updated.createdAt
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    await user_service.delete_user(user_id)
    return None
