from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class EmailDestino(Base):
    __tablename__ = "emails_destino"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    email = Column(String(100), nullable=False)

    usuario = relationship("Usuario", back_populates="emails")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String(14), unique=True, index=True)
    name = Column(String(100))

    credencial = relationship("CredenciaisVivo", back_populates="usuario", uselist=False)
    empresas = relationship("Empresa", back_populates="usuario")
    emails = relationship("EmailDestino", back_populates="usuario")


class CredenciaisVivo(Base):
    __tablename__ = "credenciais_vivo"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    cpf = Column(String(14))
    name = Column(String(100))
    email = Column(String(100))
    senha = Column(String(100))

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