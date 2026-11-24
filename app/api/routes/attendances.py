from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import require_internal_token
from app.core.config import get_settings
from app.database.connection import get_db
from app.models import Attendance, Classification, Routing
from app.schemas.attendance import AttendanceCreate, AttendanceDetail, AttendanceList, AttendanceListItem, AttendanceResponse
from app.schemas.classification import ClassificationOut
from app.schemas.routing import InternalRoutingUpdate, RoutingOut
from app.services.ai_service import AIConfigurationError, AIService, AIServiceError, get_ai_service
from app.services.routing_service import RoutingService, RoutingServiceError, get_routing_service

router = APIRouter(prefix="/api/v1", tags=["attendances"])
VALID_ROUTING_STATUSES = {"completed", "failed"}


def _classification_payload(classification: Classification) -> dict:
    return {
        "id": classification.id,
        "category": classification.category,
        "department": classification.department,
        "priority": classification.priority,
        "sentiment": classification.sentiment,
        "summary": classification.summary,
        "confidence": classification.confidence,
        "requires_human_review": classification.requires_human_review,
        "reason": classification.reason,
        "review_reason": classification.review_reason,
        "model_name": classification.model_name,
        "prompt_version": classification.prompt_version,
    }


def _routing_payload(routing: Routing | None) -> RoutingOut | None:
    return RoutingOut.model_validate(routing) if routing else None


def _response(attendance: Attendance, message: str) -> AttendanceResponse:
    return AttendanceResponse(
        id=attendance.id,
        status=attendance.status,
        message=message,
        classification=ClassificationOut.model_validate(_classification_payload(attendance.classification)) if attendance.classification else None,
        routing=_routing_payload(attendance.routing),
        created_at=attendance.created_at,
    )


async def _dispatch(db: Session, attendance: Attendance, routing: Routing, service: RoutingService) -> None:
    settings = get_settings()
    if not settings.n8n_webhook_url:
        routing.status = "pending"
        routing.error_message = None
        attendance.status = "classified"
        db.commit()
        return

    claim = db.execute(
        update(Routing)
        .where(Routing.id == routing.id, Routing.status.in_(["pending", "failed"]))
        .values(
            status="in_progress",
            error_message=None,
            attempts=Routing.attempts + 1,
            updated_at=datetime.now(timezone.utc),
        )
    )
    if claim.rowcount != 1:
        db.refresh(routing)
        db.refresh(attendance)
        return
    db.refresh(routing)
    attendance.status = "routing"
    db.commit()

    payload = {
        "attendance_id": attendance.id,
        "idempotency_key": routing.idempotency_key,
        "department": routing.department,
        "priority": attendance.classification.priority,
        "summary": attendance.classification.summary,
        "requires_human_review": attendance.classification.requires_human_review,
        "classification": _classification_payload(attendance.classification),
    }
    try:
        result = await service.dispatch(payload)
        if result is None:
            routing.status = "pending"
            attendance.status = "classified"
            db.commit()
            return
        db.refresh(routing)
        if routing.status != "completed":
            routing.status = "completed"
            routing.execution_id = result.get("execution_id") or routing.execution_id
            routing.completed_at = datetime.now(timezone.utc)
        routing.error_message = None
        attendance.status = "routed"
    except RoutingServiceError as exc:
        db.refresh(routing)
        if routing.status != "completed":
            routing.status = "failed"
            routing.error_message = str(exc)
            attendance.status = "routing_failed"
    db.commit()


@router.post("/attendances", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
    routing_service: RoutingService = Depends(get_routing_service),
):
    attendance = Attendance(
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email) if payload.customer_email else None,
        source=payload.source,
        original_message=payload.message.strip(),
        status="processing",
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    try:
        classification, model_name = await ai_service.classify(attendance.original_message)
    except AIConfigurationError as exc:
        attendance.status = "classification_failed"
        db.commit()
        raise HTTPException(status_code=503, detail={"message": str(exc), "attendance_id": attendance.id}) from exc
    except AIServiceError as exc:
        attendance.status = "classification_failed"
        db.commit()
        raise HTTPException(status_code=502, detail={"message": str(exc), "attendance_id": attendance.id}) from exc

    review_reason = None
    needs_review = classification.requires_human_review
    if classification.confidence < get_settings().ai_confidence_threshold:
        needs_review = True
        review_reason = f"Confiança abaixo do limite configurado ({get_settings().ai_confidence_threshold:.2f})."
    elif classification.requires_human_review:
        review_reason = classification.reason

    record = Classification(
        attendance_id=attendance.id,
        category=classification.category.value,
        department=classification.department.value,
        priority=classification.priority.value,
        sentiment=classification.sentiment.value,
        summary=classification.summary,
        confidence=classification.confidence,
        requires_human_review=needs_review,
        reason=classification.reason,
        review_reason=review_reason,
        model_name=model_name,
        prompt_version="1.0",
    )
    routing = Routing(
        attendance_id=attendance.id,
        department=classification.department.value,
        status="held" if needs_review else "pending",
        idempotency_key=f"attendance:{attendance.id}:routing",
    )
    attendance.classification = record
    attendance.routing = routing
    attendance.status = "pending_review" if needs_review else "classified"
    db.commit()
    db.refresh(attendance)

    if needs_review:
        return _response(attendance, "Classificação concluída; este atendimento aguarda revisão humana.")

    await _dispatch(db, attendance, routing, routing_service)
    db.refresh(attendance)
    return _response(attendance, "Classificação concluída; encaminhamento registrado." if attendance.status == "routed" else "Classificação concluída; encaminhamento pendente ou indisponível.")


@router.get("/attendances", response_model=AttendanceList)
def list_attendances(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    department: str | None = None,
    priority: str | None = None,
    sentiment: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    requires_human_review: bool | None = None,
    search: str | None = Query(default=None, max_length=200),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    statement = select(Attendance).options(joinedload(Attendance.classification), joinedload(Attendance.routing))
    count_statement = select(func.count(Attendance.id)).select_from(Attendance)
    filters = []
    if category:
        filters.append(Attendance.classification.has(Classification.category == category))
    if department:
        filters.append(Attendance.classification.has(Classification.department == department))
    if priority:
        filters.append(Attendance.classification.has(Classification.priority == priority))
    if sentiment:
        filters.append(Attendance.classification.has(Classification.sentiment == sentiment))
    if status_filter:
        filters.append(Attendance.status == status_filter)
    if requires_human_review is not None:
        filters.append(Attendance.classification.has(Classification.requires_human_review.is_(requires_human_review)))
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Attendance.id.ilike(term), Attendance.customer_name.ilike(term), Attendance.customer_email.ilike(term), Attendance.original_message.ilike(term), Attendance.classification.has(Classification.summary.ilike(term))))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    order = Attendance.created_at.desc() if sort == "desc" else Attendance.created_at.asc()
    rows = db.scalars(statement.order_by(order).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return AttendanceList(items=[AttendanceListItem.model_validate(row) for row in rows], total=total, page=page, page_size=page_size)


@router.get("/attendances/{attendance_id}", response_model=AttendanceDetail)
def get_attendance(attendance_id: str, db: Session = Depends(get_db)):
    attendance = db.scalar(
        select(Attendance).options(joinedload(Attendance.classification), joinedload(Attendance.routing)).where(Attendance.id == attendance_id)
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado.")
    return AttendanceDetail.model_validate(attendance)


@router.get("/classifications", response_model=list[ClassificationOut])
def list_classifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(Classification).order_by(Classification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return [ClassificationOut.model_validate(_classification_payload(row)) for row in rows]


@router.post("/attendances/{attendance_id}/dispatch", response_model=AttendanceResponse)
async def retry_dispatch(
    attendance_id: str,
    db: Session = Depends(get_db),
    routing_service: RoutingService = Depends(get_routing_service),
):
    attendance = db.scalar(
        select(Attendance).options(joinedload(Attendance.classification), joinedload(Attendance.routing)).where(Attendance.id == attendance_id)
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado.")
    if not attendance.classification or not attendance.routing:
        raise HTTPException(status_code=409, detail="O atendimento ainda não possui classificação encaminhável.")
    if attendance.classification.requires_human_review:
        raise HTTPException(status_code=409, detail="O encaminhamento está bloqueado até a revisão humana.")
    if attendance.routing.status == "completed":
        return _response(attendance, "Este atendimento já foi encaminhado.")
    if attendance.routing.status in {"held", "in_progress"}:
        raise HTTPException(status_code=409, detail="O encaminhamento não pode ser repetido no estado atual.")

    await _dispatch(db, attendance, attendance.routing, routing_service)
    db.refresh(attendance)
    return _response(attendance, "Nova tentativa de encaminhamento concluída." if attendance.status == "routed" else "Nova tentativa registrada; o encaminhamento permanece pendente ou falhou.")


@router.post("/internal/attendances/{attendance_id}/route", response_model=RoutingOut, dependencies=[Depends(require_internal_token)])
def register_routing(attendance_id: str, payload: InternalRoutingUpdate, db: Session = Depends(get_db)):
    if payload.status not in VALID_ROUTING_STATUSES:
        raise HTTPException(status_code=422, detail="Status de encaminhamento inválido.")
    attendance = db.scalar(
        select(Attendance).options(joinedload(Attendance.classification), joinedload(Attendance.routing)).where(Attendance.id == attendance_id)
    )
    if not attendance or not attendance.routing or not attendance.classification:
        raise HTTPException(status_code=404, detail="Atendimento encaminhável não encontrado.")
    if attendance.classification.requires_human_review:
        raise HTTPException(status_code=409, detail="Atendimentos em revisão humana não podem ser encaminhados automaticamente.")
    routing = attendance.routing
    if payload.department.value != routing.department:
        raise HTTPException(status_code=409, detail="O departamento informado não corresponde à classificação.")
    if routing.status == "completed":
        return RoutingOut.model_validate(routing)

    routing.status = payload.status
    routing.execution_id = payload.execution_id or routing.execution_id
    routing.error_message = payload.error_message[:1000] if payload.error_message else None
    if payload.status == "completed":
        routing.completed_at = datetime.now(timezone.utc)
        attendance.status = "routed"
        routing.error_message = None
    else:
        attendance.status = "routing_failed"
    db.commit()
    db.refresh(routing)
    return RoutingOut.model_validate(routing)
