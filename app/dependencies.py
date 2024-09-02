from fastapi import Depends, Header, UploadFile, HTTPException
from fastapi_users.jwt import SecretType, decode_jwt, generate_jwt
from loguru import logger

from app.db.base import AsyncSession, get_session
from app.db.tables import User
from app.services.auth import fastapi_users, get_user_manager
from app.services.auth import auth_backend, get_jwt_strategy

_strategy = get_jwt_strategy()
get_current_user = fastapi_users.current_user(active=True)
get_current_superuser = fastapi_users.current_user(active=True, superuser=True)


async def get_current_user_websocket(
        token: str,
        user_manager=Depends(get_user_manager)
):
    return await _strategy.read_token(token, user_manager)


def validate_item(item_raw: UploadFile):
    item_raw.file.seek(0, 2)
    file_size = item_raw.file.tell()
    item_raw.file.seek(0)

    if file_size > 100 * 1024 * 1024:  # 100 MB
        raise HTTPException(status_code=400, detail="File too large")
    return item_raw

