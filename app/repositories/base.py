from typing import Self
from typing import TypedDict

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi.params import Depends as DependsClass
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import ColumnOperators
from sqlalchemy import exc
from sqlalchemy import ScalarResult
from sqlalchemy import select
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute as TableAttr

from app.db.base import Base as BaseTable
from app.db.base import get_session


class TableAttributeWithSubqueryLoad(TypedDict):
    parent: TableAttr
    children: list[TableAttr]


type TableAttributesType = (
    TableAttr
    | TableAttributeWithSubqueryLoad
    | list[TableAttr | TableAttributeWithSubqueryLoad]
)


class BaseRepository[Table: BaseTable]:
    base_table: Table

    def __init__(
        self,
        response: Response = Response,
        session: AsyncSession = Depends(get_session),
    ):
        self.response = response
        self._session_creator = None
        self.session = None
        self._commit_and_close = False
        if not isinstance(session, DependsClass):
            self.session = session
            self._commit_and_close = True

    @classmethod
    async def init(cls, response: Response, session: AsyncSession):
        return cls(response=response, session=session)

    async def get(self, *args) -> Table:
        raise NotImplementedError

    async def _get_many(
        self, page: int = 0, count: int = 1000, **filters
    ) -> ScalarResult[Table]:
        query = self._get_many_query(page, count, **filters)
        return await self.session.scalars(query)

    def _get_many_query(
        self,
        page: int = 0,
        count: int = 1000,
        order_by: ColumnOperators | None = None,
        **filters,
    ) -> Select:
        offset = page * count
        query = select(self.base_table)
        query = self._query_filter(query, **filters)
        if order_by is None:
            query = query.order_by(self.base_table.id.desc())
        else:
            query = query.order_by(order_by)
        query = query.offset(offset).limit(count)
        return query

    @staticmethod
    def _query_select_in_load(
        query: Select, table_attributes: TableAttributesType
    ) -> Select:
        if not isinstance(table_attributes, list):
            table_attributes = [table_attributes]
        select_in_loads = []
        for table_attr in table_attributes:
            if isinstance(table_attr, dict):
                select_in_load = selectinload(table_attr["parent"])
                for table_attr_child in table_attr["children"]:
                    select_in_load.subqueryload(table_attr_child)
                select_in_loads.append(select_in_load)
            else:
                select_in_loads.append(selectinload(table_attr))
        query = query.options(*select_in_loads)
        return query

    def _select_in_load(self, select_in_load: TableAttributesType) -> Select:
        query = select(self.base_table)
        return self._query_select_in_load(query, select_in_load)

    async def _get_one(
        self,
        select_in_load: TableAttributesType | None = None,
        mute_not_found_exception: bool = False,
        **filters,
    ) -> Table:
        query = self._filter(**filters)
        if select_in_load is not None:
            query = self._query_select_in_load(query, select_in_load)
        obj = await self.session.scalar(query)

        if obj is None and not mute_not_found_exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return obj

    def _filter(self, **kwargs) -> Select:
        query = select(self.base_table)
        return self._query_filter(query, **kwargs)

    @staticmethod
    def _query_filter(query, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                query = query.filter_by(**{key: value})
        return query

    def _like_filter(self, **kwargs) -> Select:
        query = select(self.base_table)
        return self._query_like_filter(query, **kwargs)

    def _query_like_filter(self, query, **kwargs):
        for key, value in kwargs.items():
            if value is None:
                continue
            filter_ = "%{}%".format(value)
            query = query.filter(getattr(self.base_table, key).like(filter_))
        return query

    async def commit(self):
        if self._commit_and_close:
            try:
                await self.session.commit()
            except exc.IntegrityError as e:
                await self.session.rollback()
                if "is not present in table" in str(e.orig):
                    message = str(e.orig).split(":  Key ")[1].strip().capitalize()
                    raise HTTPException(status_code=404, detail=message)
                logger.exception(e)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    async def _update(
        self,
        primary_key: int,
        object_schema: BaseModel | None = None,
        write_none: bool = False,
        do_commit: bool = True,
        **kwargs,
    ) -> Table:
        obj = await self._get_one(id=primary_key)
        await self._update_obj(obj, object_schema, write_none, do_commit, **kwargs)
        return await self._get_one(id=primary_key)

    async def _update_obj(
        self,
        obj: Table,
        object_schema: BaseModel | None = None,
        write_none: bool = False,
        do_commit: bool = True,
        **kwargs,
    ) -> Table:
        if object_schema is None:
            object_schema = {}
        else:
            object_schema = object_schema.model_dump()
        modified = False
        for key, value in (object_schema | kwargs).items():
            attr = getattr(obj, key)
            if not write_none and value is None:
                continue
            field_is_modified = attr != value
            setattr(obj, key, value)

            modified = modified or field_is_modified
        self.session.add(obj)
        if do_commit:
            await self.commit()
        else:
            await self.session.flush([obj])
        if not modified:
            self.response.status_code = status.HTTP_304_NOT_MODIFIED
        return obj

    async def _create(
        self, model: Table | None = None, do_commit: bool = True, **kwargs
    ) -> Table:
        if model is None:
            model = self.base_table(**kwargs)
        self.session.add(model)
        if do_commit:
            await self.commit()
        else:
            await self.session.flush([model])
        self.response.status_code = status.HTTP_201_CREATED
        return model

    async def _delete(self, primary_key: int):
        obj = await self._get_one(id=primary_key)
        await self._delete_obj(obj)

    async def _delete_obj(self, obj: Table):
        await self.session.delete(obj)
        await self.commit()
        self.response.status_code = status.HTTP_204_NO_CONTENT

    async def __aenter__(self) -> Self:
        if self.session is None:
            self._session_creator = get_session()
            self.session = await anext(self._session_creator)
            self._commit_and_close = True
        return self

    async def __aexit__(self, *exc_info):
        if self._commit_and_close:
            try:
                self.session = await anext(self._session_creator)
            except StopAsyncIteration:
                pass

    async def child(
        self, response: Response | None = None, session: AsyncSession | None = None
    ) -> Self:
        if session is not None:
            self.session = session
            self._commit_and_close = False
        if response is not None:
            self.response = response
        return self
