from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String, unique=True, index=True)
    name = Column(String)

    credencial = relationship("CredencialVivo", back_populates="usuario", uselist=False)
    empresas = relationship("Empresa", back_populates="usuario")


class CredencialVivo(Base):
    __tablename__ = "credenciais_vivo"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    cpf = Column(String)
    name=Column(String)
    senha = Column(String)

    usuario = relationship("Usuario", back_populates="credencial")


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    cnpj = Column(String(18), nullable=False)
    nome_empresa = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="empresas")
    faturas = relationship("Fatura", back_populates="empresa")


class Fatura(Base):
    __tablename__ = "faturas"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    mes_referencia = Column(String(7))
    status = Column(
        Enum("paga", "aberta", "isenta", "erro", name="status_fatura")
    )
    caminho_pdf = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="faturas")