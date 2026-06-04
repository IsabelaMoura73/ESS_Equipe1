from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.room import Room, RoomMaintenanceStatus
from models.user import User, UserRole
from schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestUpdate

def get_teacher_or_raise(db: Session, teacher_cpf: str) -> User:
    user = db.query(User).filter(User.cpf == teacher_cpf).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.tipo != UserRole.DOCENTE:
        raise HTTPException(status_code=403, detail="Apenas docentes podem gerenciar solicitações de manutenção")
    if not user.status:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return user

def create_maintenance_request(db: Session, teacher_cpf: str, data: MaintenanceRequestCreate):
    teacher = get_teacher_or_raise(db, teacher_cpf)

    room = db.query(Room).filter(Room.name == data.room).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.maintenance_status == RoomMaintenanceStatus.yes:
        raise HTTPException(status_code=400, detail="Sala em manutenção")

    existing = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.room == data.room,
        MaintenanceRequest.teacher_cpf == teacher_cpf,
        MaintenanceRequest.status == MaintenanceStatus.pending
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe uma solicitação pendente para esta sala")

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

def list_maintenance_requests(db: Session, teacher_cpf: str, status: str = None):
    get_teacher_or_raise(db, teacher_cpf)
    query = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.teacher_cpf == teacher_cpf
    )
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    return query.all()

def update_maintenance_request(db: Session, request_id: int, teacher_cpf: str, data: MaintenanceRequestUpdate):
    get_teacher_or_raise(db, teacher_cpf)
    request = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.id == request_id,
        MaintenanceRequest.teacher_cpf == teacher_cpf
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if request.status != MaintenanceStatus.pending:
        raise HTTPException(status_code=400, detail="Só é possível editar solicitações pendentes")
    request.description = data.description
    db.commit()
    db.refresh(request)
    return request

def delete_maintenance_request(db: Session, request_id: int, teacher_cpf: str):
    get_teacher_or_raise(db, teacher_cpf)
    request = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.id == request_id,
        MaintenanceRequest.teacher_cpf == teacher_cpf
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if request.status != MaintenanceStatus.pending:
        raise HTTPException(status_code=400, detail="Só é possível excluir solicitações pendentes")
    db.delete(request)
    db.commit()