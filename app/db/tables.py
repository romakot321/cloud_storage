import datetime as dt
import uuid
from fastapi_users.db import SQLAlchemyBaseUserTable

from sqlalchemy import bindparam
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import text
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped as M
from sqlalchemy.orm import mapped_column as column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.associationproxy import AssociationProxy

from app.db.base import Base


class BaseMixin:
    @declared_attr.directive
    def __tablename__(cls):
        letters = ['_' + i.lower() if i.isupper() else i for i in cls.__name__]
        return ''.join(letters).lstrip('_') + 's'

    created_at: M[dt.datetime] = column(server_default=func.now())
    updated_at: M[dt.datetime] = column(
        server_default=func.now(), onupdate=func.now()
    )
    id: M[int] = column(primary_key=True, index=True)


class OwnableObjectMixin(BaseMixin):
    owner_id: M[int] = column(ForeignKey('users.id', ondelete="CASCADE"))  # aka owner
    editor_id: M[int | None] = column(ForeignKey('users.id', ondelete="CASCADE"), nullable=True)

    @declared_attr
    def creator(cls) -> M['User']:
        return relationship("User", foreign_keys=[cls.owner_id], lazy='noload')

    @declared_attr
    def editor(cls) -> M['User']:
        return relationship("User", foreign_keys=[cls.editor_id], lazy='noload')


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id: M[int] = column(primary_key=True, index=True)
    name: M[str]

    items: M[list['Item']] = relationship(lazy='noload', back_populates='owner', cascade="all, delete-orphan")


class Item(BaseMixin, Base):
    id: M[uuid.UUID] = column(primary_key=True, index=True, server_default=text('gen_random_uuid()'))
    name: M[str]
    filename: M[str]
    owner_id: M[int] = column(ForeignKey('users.id'))

    owner: M['User'] = relationship(lazy='noload', back_populates='items', foreign_keys=[owner_id])

