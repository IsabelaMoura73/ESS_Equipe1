# backend/routes/room.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.room import Room
from schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomListResponse

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=201)
def create_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    existing_room = db.query(Room).filter(Room.name == room_data.name).first()
    if existing_room:
        raise HTTPException(
            status_code=409,
            detail=f"Já existe uma sala com o nome '{room_data.name}'"
        )

    new_room = Room(
        name=room_data.name,
        capacity=room_data.capacity,
        description=room_data.description,
        computers=room_data.computers,
        maintenance_status=room_data.maintenance_status,
        is_reserved=False
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room


@router.get("/", response_model=RoomListResponse)
def list_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Room)

    if name:
        query = query.filter(Room.name.ilike(f"%{name}%"))

    total = query.count()
    rooms = query.offset(skip).limit(limit).all()

    return {"total": total, "rooms": rooms}


# Rotas estáticas devem vir ANTES de /{room_name}
@router.get("/available/list", response_model=List[RoomResponse])
def list_available_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).filter(Room.is_reserved == False).all()
    return rooms


@router.get("/maintenance/list", response_model=List[RoomResponse])
def list_rooms_in_maintenance(db: Session = Depends(get_db)):
    from models.room import RoomMaintenanceStatus
    rooms = db.query(Room).filter(
        Room.maintenance_status.in_([
            RoomMaintenanceStatus.yes,
            RoomMaintenanceStatus.scheduled
        ])
    ).all()
    return rooms


@router.get("/{room_name}", response_model=RoomResponse)
def get_room(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Sala '{room_name}' não encontrada"
        )
    return room


@router.put("/{room_name}", response_model=RoomResponse)
def update_room(room_name: str, room_data: RoomUpdate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Sala '{room_name}' não encontrada"
        )

    if room.is_reserved:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível editar a sala '{room.name}' que está reservada"
        )

    if room_data.name and room_data.name != room.name:
        existing_room = db.query(Room).filter(Room.name == room_data.name).first()
        if existing_room:
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma sala com o nome '{room_data.name}'"
            )

    update_data = room_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)

    db.commit()
    db.refresh(room)

    return room


@router.delete("/{room_name}", status_code=204)
def delete_room(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Sala '{room_name}' não encontrada"
        )

    if room.is_reserved:
        raise HTTPException(
            status_code=400,
            detail="Não é possível remover a sala que está reservada"
        )

    db.delete(room)
    db.commit()

    return None


@router.patch("/{room_name}/reserve", response_model=RoomResponse)
def mark_room_reserved(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Sala '{room_name}' não encontrada"
        )

    room.is_reserved = True
    db.commit()
    db.refresh(room)

    return room


@router.patch("/{room_name}/unreserve", response_model=RoomResponse)
def mark_room_unreserved(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Sala '{room_name}' não encontrada"
        )

    room.is_reserved = False
    db.commit()
    db.refresh(room)

    return room
