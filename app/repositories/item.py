from sqlalchemy import select

from .base import BaseRepository
from app.db.tables import Item


class ItemRepository(BaseRepository):
    base_table = Item

    async def create(self, model: Item) -> Item:
        return await self._create(model)

    async def get_one(
            self,
            item_id: int | None = None,
            item_email: str | None = None,
            mute_not_found_exception: bool = False
    ) -> Item:
        filters = {k: v for k, v in (('id', item_id), ('email', item_email)) if v is not None}
        return await self._get_one(**filters, mute_not_found_exception=mute_not_found_exception)

    async def get_many(self, **filters) -> list[Item]:
        return list(await self._get_many(**filters))

    async def update(self, item_id: int, **fields) -> Item:
        return await self._update(item_id, **fields)

    async def delete(self, item_id: int) -> None:
        await self._delete(item_id)

    async def get_owner_id(self, item_id: int) -> int | None:
        query = select(Item.owner_id).filter_by(id=item_id)
        return await self.session.scalar(query)


