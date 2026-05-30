"""
Endpoints da feature maintenance check:

  GET  /api/maintenance/admin/requests          → lista todas as solicitações
  PUT  /api/maintenance/admin/{id}/confirm      → confirma uma solicitação
  PUT  /api/maintenance/admin/{id}/deny         → nega uma solicitação

A lógica de negócio está em services/maintenance_check.py.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.maintenance_check import (
    MaintenanceCheckResponse,
    MaintenanceConfirmRequest,
    MaintenanceDenyRequest,
)
from services.maintenance_check import (
    confirm_maintenance,
    deny_maintenance,
    list_maintenance_requests,
)

router = APIRouter(prefix="/api/maintenance/admin", tags=["maintenance-check"])


# ── GET /requests ─────────────────────────────────────────────────────────────

@router.get("/requests", response_model=List[MaintenanceCheckResponse])
def list_all_requests(db: Session = Depends(get_db)):
    """Cenário 1 — admin visualiza todas as solicitações de manutenção."""
    return list_maintenance_requests(db)


# ── PUT /{id}/confirm ─────────────────────────────────────────────────────────

@router.put("/{request_id}/confirm", response_model=MaintenanceCheckResponse)
def confirm_request(
    request_id: int,
    data: MaintenanceConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Cenário 2 → confirma normalmente (sem conflitos).
    Cenário 4 → avisa sobre pendentes (force=False) ou nega-os automaticamente (force=True).
    Cenário 5 → bloqueia quando há reservas confirmadas no período.
    """
    return confirm_maintenance(db, request_id, data)


# ── PUT /{id}/deny ────────────────────────────────────────────────────────────

@router.put("/{request_id}/deny", response_model=MaintenanceCheckResponse)
def deny_request(
    request_id: int,
    data: MaintenanceDenyRequest = MaintenanceDenyRequest(),
    db: Session = Depends(get_db),
):
    """Cenário 3 — nega a solicitação; sala permanece disponível para reservas."""
    return deny_maintenance(db, request_id, data)
