
from fastapi import Depends, APIRouter

from app.db.tables import User
from app.schemas.auth import (
    AuthUserCreateSchema,
    AuthUserReadSchema,
    AuthUserUpdateSchema,
)
from app.services.auth import (
    auth_backend,
    fastapi_users,
)
from app.dependencies import get_current_user


router = APIRouter(prefix="/api/auth", tags=["Auth"])

router.include_router(fastapi_users.get_auth_router(auth_backend))
router.include_router(
    fastapi_users.get_register_router(AuthUserReadSchema, AuthUserCreateSchema),
)
router.include_router(
    fastapi_users.get_users_router(AuthUserReadSchema, AuthUserUpdateSchema),
    prefix="/user",
)


@router.get("/me", response_model=AuthUserReadSchema)
async def get_user_by_token(user: User = Depends(get_current_user)):
    return user
