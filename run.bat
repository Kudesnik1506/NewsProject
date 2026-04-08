@echo off
chcp 65001 >nul
set PYTHONUTF8=1
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0python\main.py" %*
