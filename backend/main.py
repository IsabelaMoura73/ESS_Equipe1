from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import users, rooms, reservations, maintenance

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Salla - Sistema de Reserva de Salas", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:1234"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["reservations"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["maintenance"])


@app.get("/")
def root():
    return {"message": "Salla API rodando!", "docs": "/docs"}
