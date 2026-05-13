import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models import Base, Produto, Estabelecimento, RegistroPreco

# --- 1. CONFIGURAÇÃO DO BANCO (CAMINHO ABSOLUTO) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "pricetracker.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

# --- 2. INICIALIZAÇÃO DO APP (IMPORTANTE: DEVE VIR ANTES DAS ROTAS) ---
app = FastAPI(title="Price Tracker API", version="3.0")

# --- 3. DEPENDÊNCIA DO BANCO ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. SCHEMAS (PYDANTIC) ---
class PrecoSchema(BaseModel):
    preco: float
    nome_detalhado: str
    imagem_url: Optional[str] = None
    em_promocao: Optional[bool] = False

    class Config:
        from_attributes = True

# --- 5. ROTAS DA API ---

@app.get("/")
def home():
    return {"status": "Sistema Online", "banco": DATABASE_PATH}

@app.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()

@app.get("/produtos/{produto_id}/precos")
def listar_precos(produto_id: int, db: Session = Depends(get_db)):
    # Busca os registros e inclui o nome do estabelecimento
    registros = db.query(RegistroPreco).filter(RegistroPreco.produto_id == produto_id).all()
    
    resultado = []
    for r in registros:
        resultado.append({
            "id": r.id,
            "preco": r.preco,
            "nome_detalhado": r.nome_detalhado,
            "data_coleta": r.data_coleta,
            "em_promocao": r.em_promocao,
            "imagem_url": r.imagem_url,
            "estabelecimento": r.estabelecimento.nome if r.estabelecimento else "Desconhecido"
        })
    return resultado

@app.post("/produtos/{produto_id}/precos")
def salvar_preco(produto_id: int, item: PrecoSchema, db: Session = Depends(get_db)):
    # Por padrão, associa ao Atacadão (ID 1) se não for especificado
    novo_registro = RegistroPreco(
        **item.dict(), 
        produto_id=produto_id, 
        estabelecimento_id=1 
    )
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    return novo_registro
# Adicione este schema para bater com o que o scraper envia
class RegistroSimples(BaseModel):
    produto_id: int
    estabelecimento_id: int
    preco: float
    nome_detalhado: str
    imagem_url: Optional[str] = None
    em_promocao: Optional[bool] = False

# NOVA ROTA PARA O SEU SCRAPER ATUAL
@app.post("/registros")
def salvar_registro_direto(item: RegistroSimples, db: Session = Depends(get_db)):
    novo_registro = RegistroPreco(**item.dict())
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    return novo_registro

@app.get("/produtos/{produto_id}/precos")
def listar_precos(produto_id: int, db: Session = Depends(get_db)):
    # Buscamos todos os preços desse produto, sem filtrar por mercado específico por enquanto
    registros = db.query(RegistroPreco).filter(RegistroPreco.produto_id == produto_id).all()
    
    if not registros:
        return []

    resultado = []
    for r in registros:
        resultado.append({
            "id": r.id,
            "preco": r.preco,
            "nome_detalhado": r.nome_detalhado,
            "data_coleta": r.data_coleta.strftime('%Y-%m-%dT%H:%M:%S') if r.data_coleta else None,
            "em_promocao": r.em_promocao,
            "imagem_url": r.imagem_url,
            "estabelecimento": r.estabelecimento.nome if r.estabelecimento else "Loja Teste"
        })
    return resultado