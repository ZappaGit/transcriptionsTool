#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Uso: ./transcribir.sh URL [opciones]   (ver: ./transcribir.sh --help)
DIR="$(cd "$(dirname "$0")" && pwd)"
exec uv run --project "$DIR" python "$DIR/transcribir.py" "$@"
