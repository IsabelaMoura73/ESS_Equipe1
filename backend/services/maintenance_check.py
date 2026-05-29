"""
Camada de serviço para a feature maintenance_check.

Responsabilidades:
  - list_maintenance_requests  → lista todas as solicitações (Cenário 1)
  - confirm_maintenance        → confirma com detecção de conflitos (Cenários 2, 4, 5)
  - deny_maintenance           → nega a solicitação (Cenário 3)

A rota em routes/maintenance_check.py delega toda a lógica de negócio
para este módulo, mantendo os endpoints finos (validação HTTP + resposta).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.maintenance_check import (
    MAINTENANCE_CHECK_MESSAGES,
    MaintenanceCheckStatus,
    ReservationConflictType,
)
from models.reservation import Reservation, ReservationStatus
from schemas.maintenance_check import MaintenanceConfirmRequest, MaintenanceDenyRequest


# ── Helpers internos ──────────────────────────────────────────────────────────

def _get_pending_request_or_raise(db: Session, request_id: int) -> MaintenanceRequest:
    """
    Busca a solicitação pelo id e valida que ela existe e está Pendente.
    Lança HTTPException 404 ou 400 conforme o caso.
    """
    request = (
        db.query(MaintenanceRequest)
        .filter(MaintenanceRequest.id == request_id)
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    if request.status != MaintenanceCheckStatus.pending:
        raise HTTPException(
            status_code=400,
            detail="Só é possível alterar solicitações com status 'Pendente'",
        )

    return request


def _detect_conflict(
    db: Session,
    room: str,
    start_dt: datetime,
    end_dt: datetime,
) -> Tuple[ReservationConflictType, List[Reservation]]:
    """
    Verifica reservas conflitantes no período da manutenção.

    Prioridade:
      1. Reservas CONFIRMADAS → bloqueia (confirmed_conflict)
      2. Reservas PENDENTES   → avisa    (pending_conflict)
      3. Sem conflito         → libera   (no_conflict)
    """
    confirmed = (
        db.query(Reservation)
        .filter(
            Reservation.room == room,
            Reservation.status == ReservationStatus.confirmed,
            Reservation.start_time <= end_dt,
            Reservation.end_time >= start_dt,
        )
        .all()
    )
    if confirmed:
        return ReservationConflictType.confirmed_conflict, confirmed

    pending = (
        db.query(Reservation)
        .filter(
            Reservation.room == room,
            Reservation.status == ReservationStatus.pending,
            Reservation.start_time <= end_dt,
            Reservation.end_time >= start_dt,
        )
        .all()
    )
    if pending:
        return ReservationConflictType.pending_conflict, pending

    return ReservationConflictType.no_conflict, []


# ── Funções públicas do serviço ───────────────────────────────────────────────

def list_maintenance_requests(db: Session) -> List[MaintenanceRequest]:
    """
    Cenário 1 — retorna todas as solicitações de manutenção cadastradas.
    Sem filtro de status: o admin visualiza inclusive as já confirmadas/negadas.
    """
    return db.query(MaintenanceRequest).all()


def confirm_maintenance(
    db: Session,
    request_id: int,
    data: MaintenanceConfirmRequest,
) -> MaintenanceRequest:
    """
    Cenário 2 → confirma normalmente quando não há conflitos.
    Cenário 4 → detecta reservas PENDENTES no período:
                  - force=False → levanta 409 com aviso e ids das reservas pendentes
                  - force=True  → nega automaticamente as pendentes e confirma
    Cenário 5 → detecta reservas CONFIRMADAS → bloqueia com 409, independente de force.
    """
    request = _get_pending_request_or_raise(db, request_id)

    # Período de manutenção: hoje até data de fim informada pelo admin
    start_dt = datetime.combine(date.today(), datetime.min.time())
    end_dt = datetime.combine(data.end_date, datetime.max.time())

    conflict_type, conflicting = _detect_conflict(db, request.room, start_dt, end_dt)

    # Cenário 5 — bloqueia quando há reservas confirmadas
    if conflict_type == ReservationConflictType.confirmed_conflict:
        raise HTTPException(
            status_code=409,
            detail=MAINTENANCE_CHECK_MESSAGES[ReservationConflictType.confirmed_conflict],
        )

    # Cenário 4 — avisa na primeira tentativa (force=False)
    if conflict_type == ReservationConflictType.pending_conflict and not data.force:
        raise HTTPException(
            status_code=409,
            detail={
                "message": MAINTENANCE_CHECK_MESSAGES[ReservationConflictType.pending_conflict],
                "pending_reservation_ids": [r.id for r in conflicting],
            },
        )

    # Cenário 4 — nega automaticamente as pendentes quando force=True
    for reservation in conflicting:
        reservation.status = ReservationStatus.denied

    # Confirma a manutenção e registra o período
    request.status = MaintenanceCheckStatus.confirmed
    request.start_date = date.today()
    request.end_date = data.end_date

    db.commit()
    db.refresh(request)
    return request


def deny_maintenance(
    db: Session,
    request_id: int,
    data: MaintenanceDenyRequest,
) -> MaintenanceRequest:
    """
    Cenário 3 — nega a solicitação; sala permanece disponível para reservas.
    O campo `data.reason` é opcional e reservado para extensões futuras.
    """
    request = _get_pending_request_or_raise(db, request_id)

    request.status = MaintenanceCheckStatus.denied

    db.commit()
    db.refresh(request)
    return request
