@echo off
rem Uso: transcribir URL [opciones]   (ver: transcribir --help)
uv run --project "%~dp0." python "%~dp0transcribir.py" %*
