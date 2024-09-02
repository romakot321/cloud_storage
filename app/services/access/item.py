from fastapi import Depends
from uuid import UUID

from app.db.tables import User, Item

from app.dependencies import get_current_user
from app.exceptions import AuthException
from app.repositories.item import ItemRepository

from app.schemas.item import ItemFiltersSchema


class ItemAccessService:
    def __init__(
        self,
        item_repository: ItemRepository = Depends(),
        current_user: User = Depends(get_current_user),
    ):
        self.item_repository = item_repository
        self.current_user = current_user

    async def filter_get_many_response(self, items: list[Item]) -> list[Item]:
        if self.current_user.is_superuser:
            return items
        for i in range(len(items)):
            if items[i].owner_id != self.current_user.id:
                items[i] = None
        return list(filter(lambda i: i is not None, items))

    @classmethod
    def validate_get_many(cls):
        async def validator(
            filters: ItemFiltersSchema = Depends(),
            self: ItemAccessService = Depends(cls),
        ):
            if filters.owner_id is not None and not self.current_user.is_superuser:
                raise AuthException()

        return Depends(validator)

    @classmethod
    def _get_base_validator(cls):
        async def validator(item_id: UUID, self: ItemAccessService = Depends(cls)):
            if self.current_user.is_superuser:
                return
            item_owner_id = await self.item_repository.get_owner_id(item_id=item_id)
            if item_owner_id != self.current_user.id:
                raise AuthException()

        return Depends(validator)

    @classmethod
    def validate_create(cls):
        async def validator(self: ItemAccessService = Depends(cls)):
            pass

        return Depends(validator)

    @classmethod
    def validate_update(cls):
        return cls._get_base_validator()

    @classmethod
    def validate_delete(cls):
        return cls._get_base_validator()

    @classmethod
    def validate_get_one(cls):
        return cls._get_base_validator()
