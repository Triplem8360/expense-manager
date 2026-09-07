from pydantic import BaseModel, Field


class LocalizedMessageSchema(BaseModel):
    message: str = Field(min_length=1)
    locale: str = Field(min_length=2, max_length=35)
