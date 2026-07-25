@echo off
title Thai SMC Dashboard
echo Starting Thai SMC Dashboard...
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install -e .
)

echo Dashboard: http://localhost:5080
python dashboard\app.py
