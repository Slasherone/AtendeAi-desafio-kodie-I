from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total: int
    classified: int
    pending_routing: int
    routed: int
    human_review: int
    routing_failed: int


class DistributionItem(BaseModel):
    key: str
    count: int


class AnalyticsDistribution(BaseModel):
    category: list[DistributionItem]
    department: list[DistributionItem]
    priority: list[DistributionItem]
    sentiment: list[DistributionItem]


class TimelineItem(BaseModel):
    date: str
    count: int


class AnalyticsTimeline(BaseModel):
    items: list[TimelineItem]
