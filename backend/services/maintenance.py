from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.room import Room, RoomMaintenanceStatus
from models.user import User, UserRole
from schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestUpdate


# ── helpers (Extract Method) ──────────────────────────────────────────────────

def get_teacher_or_raise(db: Session, teacher_cpf: str) -> User:
    user = db.query(User).filter(User.cpf == teacher_cpf).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.tipo != UserRole.DOCENTE:
        raise HTTPException(status_code=403, detail="Apenas docentes podem gerenciar solicitações de manutenção")
    if not user.status:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return user


def get_room_or_raise(db: Session, room_name: str) -> Room:
    """Extract Method: busca de sala e validação isoladas em um único lugar."""
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.maintenance_status == RoomMaintenanceStatus.yes:
        raise HTTPException(status_code=400, detail="Sala em manutenção")
    return room


def get_pending_request_or_raise(
    db: Session, request_id: int, teacher_cpf: str, action: str = "editar"
) -> MaintenanceRequest:
    """
    Extract Method: lógica duplicada entre update e delete centralizada aqui.
    Busca a solicitação do professor e garante que está pendente.
    """
    request = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.id == request_id,
        MaintenanceRequest.teacher_cpf == teacher_cpf,
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if request.status != MaintenanceStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Só é possível {action} solicitações pendentes",
        )
    return request


def has_pending_request(db: Session, room_name: str, teacher_cpf: str) -> bool:
    """
    Extract Method: condição de duplicidade isolada — antes ficava inline
    dentro de create_maintenance_request com query + if embutidos.
    """
    return db.query(MaintenanceRequest).filter(
        MaintenanceRequest.room == room_name,
        MaintenanceRequest.teacher_cpf == teacher_cpf,
        MaintenanceRequest.status == MaintenanceStatus.pending,
    ).first() is not None


# ── serviços públicos ─────────────────────────────────────────────────────────

def create_maintenance_request(
    db: Session, teacher_cpf: str, data: MaintenanceRequestCreate
):
    teacher = get_teacher_or_raise(db, teacher_cpf)
    room = get_room_or_raise(db, data.room)           # usa helper extraído

    if has_pending_request(db, data.room, teacher_cpf):  # usa helper extraído
        raise HTTPException(
            status_code=400,
            detail="Já existe uma solicitação pendente para esta sala",
        )

    new_request = MaintenanceRequest(
        teacher_cpf=teacher_cpf,
        teacher_name=teacher.nome,
        room=data.room,
        description=data.description,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


def list_maintenance_requests(
    db: Session, teacher_cpf: str, status: str = None
):
    get_teacher_or_raise(db, teacher_cpf)
    query = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.teacher_cpf == teacher_cpf
    )
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    return query.all()


def update_maintenance_request(
    db: Session, request_id: int, teacher_cpf: str, data: MaintenanceRequestUpdate
):
    get_teacher_or_raise(db, teacher_cpf)
    request = get_pending_request_or_raise(db, request_id, teacher_cpf, action="editar")

    request.description = data.description
    db.commit()
    db.refresh(request)
    return request


def delete_maintenance_request(
    db: Session, request_id: int, teacher_cpf: str
):
    get_teacher_or_raise(db, teacher_cpf)
    request = get_pending_request_or_raise(db, request_id, teacher_cpf, action="excluir")

    db.delete(request)
    db.commit()