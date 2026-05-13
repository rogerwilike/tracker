# 📦 Price Tracker - Plataforma de Monitoramento de Preços
### Projeto UNIVESP | Desenvolvido com Python, FastAPI, SQLite e Streamlit

---

## 📋 Pré-requisitos

Antes de rodar o projeto, você precisa ter instalado:

### 1. Python 3.10 ou superior
- Download: https://www.python.org/downloads/
- ⚠️ Durante a instalação, marque a opção **"Add Python to PATH"**
- Verifique a instalação no terminal:
  ```
  python --version
  ```

### 2. pip (gerenciador de pacotes do Python)
- Já vem instalado com o Python.
- Verifique com:
  ```
  pip --version
  ```

---

## 📁 Estrutura do Projeto

```
pricetracker/
│
├── main.py                  # API FastAPI
├── models.py                # Modelos do Banco de Dados (SQLAlchemy)
├── seed.py                  # Popula o banco com dados iniciais
├── scraper_atacadao.py      # Coleta de preços do Atacadão
├── dashboard.py             # Dashboard Streamlit
├── run.bat                  # Script para iniciar tudo automaticamente
└── pricetracker.db          # Banco de dados SQLite (gerado automaticamente)
```

---

## ⚙️ Instalação das Dependências

Abra o terminal na pasta do projeto e rode o comando abaixo:

```bash
pip install fastapi uvicorn sqlalchemy pydantic requests beautifulsoup4 selenium streamlit pandas plotly
```

### Descrição de cada biblioteca:

| Biblioteca       | Função                                              |
|------------------|-----------------------------------------------------|
| fastapi          | Framework para criar a API REST                     |
| uvicorn          | Servidor ASGI para rodar o FastAPI                  |
| sqlalchemy       | ORM para gerenciar o banco de dados SQLite          |
| pydantic         | Validação de dados da API                           |
| requests         | Fazer requisições HTTP (scraper e seed)             |
| beautifulsoup4   | Parsing de HTML para web scraping                   |
| selenium         | Automação de navegador para sites dinâmicos         |
| streamlit        | Framework para criar o dashboard visual             |
| pandas           | Manipulação e análise de dados                      |
| plotly           | Geração de gráficos interativos                     |

---

## 🚀 Como Rodar o Projeto

### Opção 1: Automático (Recomendado)
Dê dois cliques no arquivo `run.bat` ou rode no terminal:
```bash
run.bat
```

### Opção 2: Manual (passo a passo)

**Terminal 1 — Iniciar a API:**
```bash
uvicorn main:app --reload
```

**Terminal 2 — Popular o banco e coletar preços:**
```bash
python seed.py
python scraper_atacadao.py
```

**Terminal 3 — Iniciar o Dashboard:**
```bash
python -m streamlit run dashboard.py
```

---

## 🌐 Acessando o Sistema

| Serviço           | URL                          |
|-------------------|------------------------------|
| Dashboard         | http://localhost:8501        |
| API               | http://127.0.0.1:8000        |
| Documentação API  | http://127.0.0.1:8000/docs   |

---

## ⚠️ Observações Importantes

1. **Cookies do Scraper:** Os cookies do Atacadão expiram periodicamente.
   Se o scraper retornar erro HTTP 403 ou timeout, atualize os cookies no arquivo `scraper_atacadao.py`.
   Para renovar:
   - Acesse www.atacadao.com.br no navegador
   - Pressione F12 → aba Network
   - Pesquise qualquer produto
   - Clique na requisição `graphql`
   - Copie os valores de `cf_clearance` e `__cf_bm`

2. **Reset do Banco:** Se precisar limpar todos os dados e começar do zero:
   ```bash
   del pricetracker.db
   python seed.py
   python scraper_atacadao.py
   ```

3. **Pasta do Projeto:** Sempre abra o terminal dentro da pasta `pricetracker` antes de rodar qualquer comando.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy, SQLite
- **Coleta de Dados:** Requests, BeautifulSoup4, Selenium
- **Frontend:** Streamlit, Plotly, Pandas
- **Banco de Dados:** SQLite (arquivo local `pricetracker.db`)

---

## 👨‍💻 Desenvolvido por
Projeto Integrador — UNIVESP  
Price Tracker: Plataforma de Monitoramento de Preços para Economia Doméstica
