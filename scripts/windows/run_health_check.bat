@echo off
cd /d %~dp0
call .venvEnvisionPerdido\Scripts\activate.bat
python scripts\health_check.py
