import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi import Depends, Request, HTTPException, Response
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.password import PasswordHelper
from fastapi_users.db import SQLAlchemyUserDatabase

from app.db.tables import User
from app.db.base import get_session

SECRET = "SECRET"

bearer_transport = BearerTransport(tokenUrl="/api/auth/login")


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


class _AuthUserModel(SQLAlchemyUserDatabase):
    pass


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


async def _get_user_db(session: AsyncSession = Depends(get_session)):
    yield _AuthUserModel(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(_get_user_db)):
    yield UserManager(user_db)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
