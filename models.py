from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"
    id       = Column(Integer, primary_key=True, index=True)
    nome     = Column(String, nullable=False)
    cidade   = Column(String)
    site_url = Column(String)
    registros = relationship("RegistroPreco", back_populates="estabelecimento")

class Produto(Base):
    __tablename__ = "produtos"
    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String, nullable=False)
    categoria = Column(String)
    unidade   = Column(String)
    registros = relationship("RegistroPreco", back_populates="produto")

class RegistroPreco(Base):
    __tablename__ = "registros_precos"
    id                 = Column(Integer, primary_key=True, index=True)
    produto_id         = Column(Integer, ForeignKey("produtos.id"))
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"))
    preco               = Column(Float)
    
    # AJUSTE CRÍTICO: DateTime com preenchimento automático (func.now())
    data_coleta        = Column(DateTime, server_default=func.now())
    
    em_promocao        = Column(Boolean, default=False)
    nome_detalhado     = Column(String)
    imagem_url         = Column(String, nullable=True)

    produto         = relationship("Produto",         back_populates="registros")
    estabelecimento = relationship("Estabelecimento", back_populates="registros")