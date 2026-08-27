from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"

class TicketStatus(str, enum.Enum):
    PENDING = "Pendiente"
    IN_PROGRESS = "En Progreso"
    COMPLETED = "Completado"

class TicketUrgency(str, enum.Enum):
    LOW = "Bajo"
    MEDIUM = "Medio"
    HIGH = "Alto"
    CRITICAL = "Crítico"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default=UserRole.CLIENT)

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descripcion = Column(Text)
    nombre_solicitante = Column(String)
    cargo_solicitante = Column(String, nullable=True)
    
    # Nuevos campos solicitados
    tipo_afectacion = Column(String) # Aplicación, Equipo
    subtipo_equipo = Column(String, nullable=True) # Computador, Cámara, Impresora (solo si es Equipo)
    tipo_solicitud = Column(String) # Fallo, Instalación
    
    urgencia = Column(String, default=TicketUrgency.LOW)
    estado = Column(String, default=TicketStatus.PENDING)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
