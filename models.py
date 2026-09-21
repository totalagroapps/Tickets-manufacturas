from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
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
    celular_solicitante = Column(String, nullable=True)
    
    # Nuevos campos solicitados
    tipo_afectacion = Column(String) # Aplicación, Equipo
    subtipo_equipo = Column(String, nullable=True) # Computador, Cámara, Impresora (solo si es Equipo)
    tipo_solicitud = Column(String) # Fallo, Instalación
    responsable = Column(String, default="Soporte") # Soporte, Desarrollo, Administrativo
    
    urgencia = Column(String, default=TicketUrgency.LOW)
    estado = Column(String, default=TicketStatus.PENDING)
    
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    fecha_cierre = Column(DateTime, nullable=True)

    gestiones = relationship("TicketGestion", back_populates="ticket", cascade="all, delete-orphan")
    adjuntos = relationship("TicketAdjunto", back_populates="ticket", cascade="all, delete-orphan")

class TicketGestion(Base):
    __tablename__ = "ticket_gestiones"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    autor = Column(String)
    nota = Column(Text)
    fecha = Column(DateTime, default=func.now())
    
    ticket = relationship("Ticket", back_populates="gestiones")

class TicketAdjunto(Base):
    __tablename__ = "ticket_adjuntos"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    nombre_archivo = Column(String)
    tipo_contenido = Column(String)
    archivo_bytes = Column(LargeBinary)
    tamano = Column(Integer, default=0)
    fecha_subida = Column(DateTime, default=func.now())
    
    ticket = relationship("Ticket", back_populates="adjuntos")

class RedConfig(Base):
    __tablename__ = "red_config"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, unique=True, index=True)
    valor = Column(Text)
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
