# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script Windows CLI (`transcribir.py`) that downloads the audio from a URL (YouTube, `.m3u8` streams, anything yt-dlp supports) or takes a local audio file, transcribes it with faster-whisper on CPU, and writes a paragraphed `.txt` to `transcripciones/`. Code, comments, CLI flags and user-facing messages are in Spanish. Keep them that way.

## Commands

Dependencies are managed with `uv` (Python >= 3.12, see `pyproject.toml` / `uv.lock`). There are no tests, linter config or build step.

```powershell
uv sync                                              # install deps into .venv
uv run python transcribir.py URL                     # run directly
.\transcribir.cmd URL --modelo medium --idioma es    # wrapper; works from any cwd
uv run python transcribir.py C:\ruta\audio.mp3       # local file, no download
```

Quick smoke test: `uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --modelo tiny` (19 s video; expected output already in `transcripciones/`).

External requirement: **ffmpeg** must be on PATH or installed via `winget install Gyan.FFmpeg`. `buscar_ffmpeg()` also looks in the WinGet Links/Packages folders under `%LOCALAPPDATA%`, because winget installs often aren't on PATH in the current shell.

## Pipeline

`main()` → `descargar_audio()` (skipped for local files) → `transcribir()` → `en_parrafos()` → write `.txt` → delete the downloaded audio (unless `--conservar-audio`).

- **Download**: yt-dlp extracts best audio and converts it with ffmpeg to mono 16 kHz 64k mp3 (the format Whisper uses). Output name template is `%(title).80B - %(id)s`, which also becomes the `.txt` name. Auth options for protected streams: `--referer` (also sets `Origin`), `--cookies-navegador`, `--cookies`. 401/403 errors print a Spanish troubleshooting hint and exit.
- **Transcription**: `WhisperModel(device="cpu", compute_type="int8")`, default model `small`. `vad_filter=True` and `condition_on_previous_text=False` are deliberate: they skip silence/music and prevent hallucinated repetition loops. Don't remove them.
- **Paragraphing**: `en_parrafos` consumes the lazy segment generator (this is where the actual transcription runs) and starts a new paragraph after a pause > 2 s or after ~600 chars ending in sentence punctuation. It prints progress every 5 s.
- `yt_dlp` and `faster_whisper` are imported lazily inside functions so `--help` stays fast.
- Local-file detection: the arg has no `://` and the path exists.
- Paths: `--salida` defaults to `transcripciones/` next to the script (`RAIZ`), not the cwd. The downloaded audio is written into that same folder and deleted afterwards. Whisper models are cached by Hugging Face Hub (first run per model downloads it).
