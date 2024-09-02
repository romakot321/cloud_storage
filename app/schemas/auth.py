from fastapi_users import schemas


class AuthUserReadSchema(schemas.BaseUser[int]):
    name: str | None = None


class AuthUserCreateSchema(schemas.BaseUserCreate):
    name: str | None = None


class AuthUserUpdateSchema(schemas.BaseUserUpdate):
    name: str | None = None
