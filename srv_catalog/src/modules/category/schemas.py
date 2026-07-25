from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field



class CategoryRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None


class CategoryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str = Field(max_length=255)
    description: str | None = None