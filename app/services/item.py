from fastapi import Depends, UploadFile
from uuid import UUID, uuid4
import functools

from app.schemas.item import ItemGetSchema, ItemCreateSchema
from app.schemas.item import ItemShortSchema, ItemFiltersSchema
from app.schemas.item import ItemUpdateSchema
from app.repositories.item import ItemRepository
from app.repositories.storage import StorageRepository
from app.services.access import ItemAccessService
from app.db.tables import Item


class ItemService:
    def __init__(
            self,
            repository: ItemRepository = Depends(),
            access_service: ItemAccessService = Depends(),
            storage_repository: StorageRepository = Depends()
    ):
        self.repository = repository
        self.access_service = access_service
        self.storage_repository = storage_repository

    async def create(self, schema: ItemCreateSchema, file: UploadFile) -> ItemShortSchema:
        system_filename = uuid4()
        path = self.storage_repository.create(file.file, str(system_filename))
        model = Item(id=system_filename, filename=file.filename, **schema.model_dump())
        model = await self.repository.create(model)
        return ItemShortSchema.model_validate(model)

    async def get_one(self, item_id: UUID):
        item = await self.repository.get_one(item_id)
        return ItemGetSchema.model_validate(item)

    def stream(self, item_filename: UUID):
        return self.storage_repository.get(str(item_filename))

    async def get_many(self, filters: ItemFiltersSchema) -> list[ItemShortSchema]:
        filters = filters.model_dump(exclude_none=True)
        models = await self.repository.get_many(**filters)
        models = await self.access_service.filter_get_many_response(models)
        return [
            ItemShortSchema.model_validate(model)
            for model in models
        ]

    async def update(self, item_id: UUID, schema: ItemUpdateSchema) -> ItemShortSchema:
        fields = schema.model_dump(exclude_none=True)
        model = await self.repository.update(item_id, **fields)
        return ItemShortSchema.model_validate(model)

    async def delete(self, item_id: UUID) -> None:
        self.storage_repository.delete(str(item_id))
        await self.repository.delete(item_id)

