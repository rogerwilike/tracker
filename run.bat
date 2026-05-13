@echo off
echo ========================================
echo   PRICE TRACKER - INICIANDO SISTEMA
echo ========================================

echo.
echo [1/4] Iniciando API (nova janela)...
start "API - Uvicorn" cmd /k "uvicorn main:app --reload"
timeout /t 5 /nobreak >nul

echo [2/4] Populando banco de dados...
python seed.py

echo.
echo [3/4] Rodando Scraper...
python scraper_atacadao.py

echo.
echo [4/4] Iniciando Dashboard (nova janela)...
start "Dashboard - Streamlit" cmd /k "python -m streamlit run dashboard.py"

echo.
echo ✅ Sistema completo rodando!
pause