from pydantic import BaseModel


class BaseFiltersSchema(BaseModel):
    page: int = 0
    count: int = 100
