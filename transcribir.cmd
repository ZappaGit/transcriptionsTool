@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Copyright (C) [YEAR] [HOLDER]
rem Uso: transcribir URL [opciones]   (ver: transcribir --help)
uv run --project "%~dp0." python "%~dp0transcribir.py" %*
