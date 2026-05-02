from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from dependencies import get_current_user, require_admin
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Room).all()


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    return room


@router.post("/", response_model=schemas.RoomOut, status_code=201)
def create_room(
    data: schemas.RoomCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    room = models.Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/{room_id}", response_model=schemas.RoomOut)
def update_room(
    room_id: int,
    data: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    db.delete(room)
    db.commit()
