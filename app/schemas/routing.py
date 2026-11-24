from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.classification import Department


class InternalRoutingUpdate(BaseModel):
    department: Department
    status: str
    execution_id: str | None = None
    error_message: str | None = None


class RoutingOut(BaseModel):
    id: str
    department: Department
    status: str
    execution_id: str | None = None
    error_message: str | None = None
    attempts: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
