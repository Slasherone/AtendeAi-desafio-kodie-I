from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Attendance, Classification, Routing
from app.schemas.analytics import AnalyticsDistribution, AnalyticsOverview, AnalyticsTimeline, DistributionItem, TimelineItem

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Attendance.id))) or 0
    classified = db.scalar(select(func.count(Attendance.id)).where(Attendance.classification.has())) or 0
    pending_routing = db.scalar(select(func.count(Routing.id)).where(Routing.status.in_(["pending", "in_progress"]))) or 0
    routed = db.scalar(select(func.count(Routing.id)).where(Routing.status == "completed")) or 0
    human_review = db.scalar(select(func.count(Classification.id)).where(Classification.requires_human_review.is_(True))) or 0
    routing_failed = db.scalar(select(func.count(Routing.id)).where(Routing.status == "failed")) or 0
    return AnalyticsOverview(
        total=total,
        classified=classified,
        pending_routing=pending_routing,
        routed=routed,
        human_review=human_review,
        routing_failed=routing_failed,
    )


@router.get("/distribution", response_model=AnalyticsDistribution)
def distribution(db: Session = Depends(get_db)):
    def counts(field: str) -> list[DistributionItem]:
        rows = db.execute(select(getattr(Classification, field), func.count(Classification.id)).group_by(getattr(Classification, field))).all()
        return [DistributionItem(key=key, count=count) for key, count in rows]

    return AnalyticsDistribution(
        category=counts("category"),
        department=counts("department"),
        priority=counts("priority"),
        sentiment=counts("sentiment"),
    )


@router.get("/timeline", response_model=AnalyticsTimeline)
def timeline(
    days: int = Query(default=14, ge=1, le=365),
    db: Session = Depends(get_db),
):
    today_utc = datetime.now(timezone.utc).date()
    start = datetime.combine(today_utc - timedelta(days=days - 1), datetime.min.time()).replace(tzinfo=timezone.utc)
    rows = db.scalars(select(Attendance.created_at).where(Attendance.created_at >= start)).all()
    totals = Counter(
        (timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc))
        .date()
        .isoformat()
        for timestamp in rows
    )
    dates = [(today_utc - timedelta(days=offset)).isoformat() for offset in reversed(range(days))]
    items = [TimelineItem(date=day, count=totals.get(day, 0)) for day in dates]
    return AnalyticsTimeline(items=items)
