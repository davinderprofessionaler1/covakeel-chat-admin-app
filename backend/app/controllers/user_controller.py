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
    if user.email and await user_service.get_user_by_login(str(user.email)):
        raise HTTPException(status_code=400, detail="Email already exists")
    user_id = await user_service.create_user(user)
    created = await user_service.get_user_by_id(user_id)
    return UserRead(
        id=str(created._id),
        username=created.username,
        email=created.email,
        name=getattr(created, "name", None),
        profile=getattr(created, "profile", None),
        createdAt=created.createdAt,
        isAdmin=getattr(created, "is_admin", False)
    )


@router.get("/me", response_model=UserRead)
async def register(user=Depends(get_current_user)):
    return UserRead(
        id=str(user._id),
        username=user.username,
        email=user.email,
        name=getattr(user, "name", None),
        profile=getattr(user, "profile", None),
        createdAt=user.createdAt,
        isAdmin=getattr(user, "is_admin", False)
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    if user_id != str(current_user._id):
        raise HTTPException(status_code=404, detail="User not found")
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(
        id=str(user._id),
        username=user.username,
        email=user.email,
        name=getattr(user, "name", None),
        profile=getattr(user, "profile", None),
        createdAt=user.createdAt,
        isAdmin=getattr(user, "is_admin", False)
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, user_update: UserUpdate, current_user=Depends(get_current_user)):
    if user_id != str(current_user._id):
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.email:
        existing = await user_service.get_user_by_login(str(user_update.email))
        if existing and str(existing._id) != user_id:
            raise HTTPException(status_code=400, detail="Email already exists")
    updated = await user_service.update_user(user_id, user_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(
        id=str(updated._id),
        username=updated.username,
        email=updated.email,
        name=getattr(updated, "name", None),
        profile=getattr(updated, "profile", None),
        createdAt=updated.createdAt,
        isAdmin=getattr(updated, "is_admin", False)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user=Depends(get_current_user)):
    if user_id != str(current_user._id):
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.delete_user(user_id)
    return None
