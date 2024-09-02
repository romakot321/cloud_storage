from pydantic import BaseModel, ConfigDict, model_validator
import datetime as dt
from itertools import groupby
import operator
from uuid import UUID

from .base import BaseFiltersSchema


class ItemGetSchema(BaseModel):
    id: UUID
    owner_id: int
    name: str
    filename: str

    model_config = ConfigDict(from_attributes=True)


class ItemCreateSchema(BaseModel):
    name: str
    owner_id: int


class ItemShortSchema(BaseModel):
    id: UUID
    owner_id: int
    name: str
    filename: str

    model_config = ConfigDict(from_attributes=True)


class ItemFiltersSchema(BaseFiltersSchema):
    name: str | None = None
    owner_id: int | None = None


class ItemUpdateSchema(BaseModel):
    name: str | None = None

