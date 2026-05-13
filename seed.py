# seed.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Produto, Estabelecimento

# --- CONFIGURAÇÃO DO BANCO (CAMINHO ABSOLUTO) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "pricetracker.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def popular_banco():
    # 1. Garante que as tabelas existam
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 2. Cadastrar Estabelecimentos (Apenas se não existirem)
        estabelecimentos = [
            {"nome": "Atacadão", "cidade": "São Paulo", "site_url": "https://www.atacadao.com.br"},
            {"nome": "Carrefour", "cidade": "São Paulo", "site_url": "https://www.carrefour.com.br"},
            {"nome": "Savegnago", "cidade": "Ribeirão Preto", "site_url": "https://www.savegnago.com.br"},
            {"nome": "Tenda Atacado", "cidade": "Guarulhos", "site_url": "https://www.tendaatacado.com.br"}
        ]

        for est in estabelecimentos:
            existe = db.query(Estabelecimento).filter_by(nome=est["nome"]).first()
            if not existe:
                novo_est = Estabelecimento(**est)
                db.add(novo_est)
                print(f"✅ Estabelecimento adicionado: {est['nome']}")

        # 3. Cadastrar Produtos (Apenas se não existirem)
        produtos_base = [
            {"nome": "Arroz",   "categoria": "Grãos",      "unidade": "kg"},
            {"nome": "Feijão",  "categoria": "Grãos",      "unidade": "kg"},
            {"nome": "Leite",   "categoria": "Laticínios", "unidade": "L"},
            {"nome": "Óleo",    "categoria": "Óleos",      "unidade": "ml"},
            {"nome": "Açúcar",  "categoria": "Grãos",      "unidade": "kg"}
        ]

        for p in produtos_base:
            existe = db.query(Produto).filter_by(nome=p["nome"]).first()
            if not existe:
                novo_p = Produto(**p)
                db.add(novo_p)
                print(f"✅ Produto adicionado: {p['nome']}")

        db.commit()
        print(f"\n🚀 Sincronização concluída! Banco em: {DATABASE_PATH}")
        
    except Exception as e:
        print(f"❌ Erro ao popular: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()