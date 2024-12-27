from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con las palabras clave
    keywords = relationship("Keyword", back_populates="user")
    
class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relación con el usuario
    user = relationship("User", back_populates="keywords")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String, unique=True)
    scraper_type = Column(String)  # Tipo de scraper a usar (ispch, etc.)
    active = Column(Boolean, default=True)  # Activo o inactivo
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime)

class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    source_type = Column(String, index=True)
    category = Column(String, index=True)
    country = Column(String, index=True)
    source_url = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    presentation_date = Column(DateTime)
    metadata_nota_url = Column(String, nullable=True)
    metadata_publicacion_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Índices únicos
    __table_args__ = (
        # Si tiene URL, validar por URL, título y fecha
        UniqueConstraint('source_url', 'title', 'presentation_date', name='uix_alerta_url_title_date'),
        # Si no tiene URL, validar por título y fecha
        UniqueConstraint('title', 'presentation_date', name='uix_alerta_title_date')
    )