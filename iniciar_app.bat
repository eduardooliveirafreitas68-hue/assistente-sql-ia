@echo off
REM Abre o Assistente SQL com IA com dois cliques (Windows).
REM Pre-requisito: ter feito a instalacao uma vez (veja o README).
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Rode uma vez: python -m venv .venv  e depois  pip install -r requirements.txt
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
echo Abrindo o app no navegador... Para fechar, feche esta janela ou aperte Ctrl+C.
streamlit run app.py
pause
