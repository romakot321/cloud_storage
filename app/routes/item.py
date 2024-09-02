from fastapi import APIRouter, Depends
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
from uuid import UUID

from app.schemas.item import ItemShortSchema
from app.schemas.item import ItemGetSchema
from app.schemas.item import ItemCreateSchema
from app.schemas.item import ItemUpdateSchema
from app.schemas.item import ItemFiltersSchema
from app.services.item import ItemService
from app.services.access import ItemAccessService
from app.db.tables import User
from app.dependencies import get_current_user, validate_item

router = APIRouter(prefix="/api/item", tags=["Item"])


@router.get(
    '',
    response_model=list[ItemShortSchema],
    dependencies=[ItemAccessService.validate_get_many()]
)
async def get_items(filters: ItemFiltersSchema = Depends(), service: ItemService = Depends()):
    return await service.get_many(filters)


@router.get(
    '/{item_id}',
    response_model=ItemGetSchema,
    dependencies=[ItemAccessService.validate_get_one()]
)
async def get_item(item_id: UUID, service: ItemService = Depends()):
    item = await service.get_one(item_id)
    stream = service.stream(item_id)
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={'Content-Disposition': f'attachment; filename="{item.filename}"'}
    )


@router.post(
    '',
    response_model=ItemShortSchema,
    status_code=201,
    dependencies=[ItemAccessService.validate_create()]
)
async def create_item(
        schema: ItemCreateSchema = Depends(),
        item_raw: UploadFile = Depends(validate_item),
        service: ItemService = Depends(),
):
    return await service.create(schema, item_raw)


@router.patch(
    '/{item_id}',
    response_model=ItemShortSchema,
    dependencies=[ItemAccessService.validate_update()]
)
async def update_item(
        item_id: UUID,
        schema: ItemUpdateSchema,
        service: ItemService = Depends()
):
    return await service.update(item_id, schema)


@router.delete(
    '/{item_id}',
    status_code=204,
    dependencies=[ItemAccessService.validate_delete()]
)
async def delete_item(item_id: UUID, service: ItemService = Depends()):
    await service.delete(item_id)

