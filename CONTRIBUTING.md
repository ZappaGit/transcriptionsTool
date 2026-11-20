# Cómo contribuir

Gracias por tu interés. Antes de empezar, lee el [código de conducta](CODE_OF_CONDUCT.md) y la [política de seguridad](SECURITY.md).

## Preparar el entorno

Requisitos: Windows, [uv](https://docs.astral.sh/uv/) y ffmpeg (`winget install Gyan.FFmpeg`).

```powershell
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
uv run python transcribir.py --help
```

## Comprobaciones

El proyecto no tiene tests unitarios. La comprobación de referencia es el smoke test: un vídeo corto de YouTube (19 s) cuya salida debe coincidir con la versión de referencia versionada en `transcripciones/`:

```powershell
uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --salida $env:TEMP\humo
```

Compara el `.txt` resultante con `transcripciones/Me at the zoo - jNQXAC9IVRw.txt`.

Notas:

- Usa el modelo por defecto (`small`). Con `tiny`, la salida cambia entre ejecuciones porque Whisper muestrea de nuevo en las ventanas de baja confianza.
- Con `small` puede cambiar alguna palabra por el mismo motivo. Repite la prueba antes de dar por buena una diferencia de una palabra.

## Convenciones

- El código, los comentarios, las opciones de línea de comandos y los mensajes al usuario están en **español**. Mantenlo así.
- Lee [CLAUDE.md](CLAUDE.md): describe la arquitectura y las decisiones que no conviene revertir. En particular:
  - `vad_filter=True` y `condition_on_previous_text=False` son deliberados; no los quites.
  - El formato `bestaudio/worst` no se cambia a `best`.
  - Los subtítulos automáticos de YouTube no se usan (solo los hechos por personas).
- Mantén las dependencias al mínimo. Si añades una, explica por qué en la descripción del PR y comprueba que su licencia sea compatible con GPLv3.
- No añadas al repositorio audio, vídeo, transcripciones, cookies, tokens, modelos ni rutas personales. Están excluidos en `.gitignore`; si necesitas una salida de referencia nueva, discútelo en un issue antes.

## Abrir un pull request

1. Crea una rama desde `main` (no trabajes directamente sobre `main`).
2. Haz cambios pequeños y con un propósito claro. Un PR por tema.
3. Ejecuta el smoke test y el `--help`, y anótalo en la plantilla del PR.
4. Abre el PR contra `main` y rellena la [plantilla](.github/pull_request_template.md).
5. Un mantenedor revisará el PR. Los checks de CodeQL deben pasar antes de fusionar.

## Licencia de las contribuciones

El proyecto se distribuye bajo [GPLv3](LICENSE). Al enviar una contribución aceptas que se publique bajo esa misma licencia. Mantén la cabecera SPDX en los ficheros nuevos:

```python
# SPDX-License-Identifier: GPL-3.0-or-later
```

## Reportar problemas

- Errores y propuestas: abre un issue con la plantilla correspondiente.
- Vulnerabilidades de seguridad: **no** las abras como issue. Sigue [SECURITY.md](SECURITY.md).
