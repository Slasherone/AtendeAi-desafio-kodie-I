from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.classification import Category, ClassificationOut, Department, Priority, Sentiment
from app.schemas.routing import RoutingOut


class AttendanceCreate(BaseModel):
    customer_name: str | None = Field(default=None, max_length=160)
    customer_email: EmailStr | None = None
    source: str = Field(default="web", min_length=1, max_length=40)
    message: str = Field(min_length=1, max_length=10000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("A mensagem não pode conter apenas espaços.")
        return normalized


class AttendanceResponse(BaseModel):
    id: str
    status: str
    message: str
    classification: ClassificationOut | None = None
    routing: RoutingOut | None = None
    created_at: datetime


class AttendanceListItem(BaseModel):
    id: str
    customer_name: str | None
    source: str
    status: str
    created_at: datetime
    classification: ClassificationOut | None = None
    routing: RoutingOut | None = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceDetail(AttendanceListItem):
    customer_email: str | None
    original_message: str
    updated_at: datetime


class AttendanceList(BaseModel):
    items: list[AttendanceListItem]
    total: int
    page: int
    page_size: int
