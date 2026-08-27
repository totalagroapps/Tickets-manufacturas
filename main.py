from fastapi import FastAPI, Depends, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional

import models
from database import engine, get_db, SessionLocal

from contextlib import asynccontextmanager

def create_default_users():
    db = SessionLocal()
    try:
        # Check if client user exists
        client_user = db.query(models.User).filter(models.User.username == "cliente").first()
        if not client_user:
            client_user = models.User(
                username="cliente",
                password_hash=get_password_hash("1234"),
                role=models.UserRole.CLIENT
            )
            db.add(client_user)

        # Check if admin user exists
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=models.UserRole.ADMIN
            )
            db.add(admin_user)

        db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    models.Base.metadata.create_all(bind=engine)
    create_default_users()
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# Para archivos estáticos si los hay (opcional)
import os
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "super_secret_key_change_in_production"
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # Check for Bearer prefix and strip it if exists, but we are setting just the token
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(models.User).filter(models.User.username == username).first()
        return user
    except JWTError:
        return None

def get_current_admin(user: models.User = Depends(get_current_user)):
    if not user or user.role != models.UserRole.ADMIN:
        return None
    return user

@app.get("/", response_class=HTMLResponse)
def root_redirect(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    if user.role == models.UserRole.ADMIN:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/tickets", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@app.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Credenciales inválidas"})
    
    access_token = create_access_token(data={"sub": user.username})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"{access_token}", httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/tickets", response_class=HTMLResponse)
def client_dashboard(request: Request, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Mostrar últimos tickets
    tickets = db.query(models.Ticket).order_by(models.Ticket.fecha_creacion.desc()).all()
    return templates.TemplateResponse(request=request, name="cliente_dashboard.html", context={"request": request, "tickets": tickets, "user": user})

@app.post("/tickets")
def create_ticket(
    request: Request,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    nombre_solicitante: str = Form(...),
    cargo_solicitante: str = Form(None),
    urgencia: str = Form(...),
    tipo_afectacion: str = Form(...),
    subtipo_equipo: str = Form(None),
    tipo_solicitud: str = Form(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    new_ticket = models.Ticket(
        titulo=titulo,
        descripcion=descripcion,
        nombre_solicitante=nombre_solicitante,
        cargo_solicitante=cargo_solicitante,
        urgencia=urgencia,
        tipo_afectacion=tipo_afectacion,
        subtipo_equipo=subtipo_equipo,
        tipo_solicitud=tipo_solicitud
    )
    db.add(new_ticket)
    db.commit()
    return RedirectResponse(url="/tickets", status_code=status.HTTP_302_FOUND)

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, user: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    tickets = db.query(models.Ticket).order_by(models.Ticket.fecha_creacion.desc()).all()
    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={"request": request, "tickets": tickets, "user": user})

@app.post("/admin/ticket/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    estado: str = Form(...),
    user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if ticket:
        ticket.estado = estado
        db.commit()
        
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
