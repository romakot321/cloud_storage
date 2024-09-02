from sqlalchemy import select

from .base import BaseRepository
from app.db.tables import User


class UserRepository(BaseRepository):
    base_table = User

    async def create(self, model: User) -> User:
        return await self._create(model)

    async def get_one(
        self,
        user_id: int | None = None,
        user_email: str | None = None,
        mute_not_found_exception: bool = False,
    ) -> User:
        filters = {
            k: v for k, v in (("id", user_id), ("email", user_email)) if v is not None
        }
        return await self._get_one(
            **filters, mute_not_found_exception=mute_not_found_exception
        )

    async def get_many(self, **filters) -> list[User]:
        return list(await self._get_many(**filters))

    async def update(self, user_id: int, **fields) -> User:
        return await self._update(user_id, **fields)

    async def delete(self, user_id: int) -> None:
        await self._delete(user_id)

    async def get_owner_id(self, user_id: int) -> int | None:
        query = select(User.owner_id).filter_by(id=user_id)
        return await self.session.scalar(query)
