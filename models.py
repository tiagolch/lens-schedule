from database import Base
from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class UtilizadorModel(Base):
  __tablename__ = "utilizadores"

  id = Column(Integer, primary_key=True, index=True)
  nome = Column(String(50), unique=True, index=True, nullable=False)
  password_hash = Column(String(255), nullable=False)

  organizadores = relationship(
      "OrganizadorModel",
      back_populates="utilizador",
      cascade="all, delete-orphan",
  )
  eventos = relationship(
      "EventoModel",
      back_populates="utilizador",
      cascade="all, delete-orphan",
  )


class OrganizadorModel(Base):
  __tablename__ = "organizadores"

  id = Column(Integer, primary_key=True, index=True)
  utilizador_id = Column(Integer, ForeignKey("utilizadores.id"), nullable=False)
  nome = Column(String(100), index=True, nullable=False)

  __table_args__ = (
      UniqueConstraint("utilizador_id", "nome", name="uq_utilizador_organizador"),
  )

  utilizador = relationship("UtilizadorModel", back_populates="organizadores")
  eventos = relationship(
      "EventoModel",
      back_populates="organizador",
      cascade="all, delete-orphan",
  )


class EventoModel(Base):
  __tablename__ = "eventos"

  id = Column(Integer, primary_key=True, index=True)
  utilizador_id = Column(Integer, ForeignKey("utilizadores.id"), nullable=False)
  nome_evento = Column(String(150), index=True, nullable=False)
  organizador_id = Column(
      Integer, ForeignKey("organizadores.id"), nullable=False
  )
  data = Column(Date, nullable=False)
  ano = Column(Integer, index=True, nullable=False)
  horario = Column(String(50), nullable=True)
  local = Column(String(150), nullable=True)
  custos = Column(Float, default=0.0)
  vendas = Column(Float, default=0.0)

  utilizador = relationship("UtilizadorModel", back_populates="eventos")
  organizador = relationship("OrganizadorModel", back_populates="eventos")
