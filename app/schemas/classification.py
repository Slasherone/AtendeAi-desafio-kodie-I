from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    question = "question"
    complaint = "complaint"
    request = "request"
    compliment = "compliment"
    other = "other"


class Department(str, Enum):
    support = "support"
    financial = "financial"
    commercial = "commercial"
    customer_service = "customer_service"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ClassificationResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category: Category
    department: Department
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    reason: str = Field(min_length=1, max_length=2000)


class ClassificationOut(ClassificationResult):
    id: str
    review_reason: str | None = None
    model_name: str | None = None
    prompt_version: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
