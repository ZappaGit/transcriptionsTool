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

Quick smoke test: `uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --salida $env:TEMP\humo` (19 s video, default `small` model; output must be identical to `transcripciones/Me at the zoo - jNQXAC9IVRw.txt`). Don't compare with `tiny`: its low-confidence windows trigger Whisper's temperature fallback (random sampling), so its output changes between runs. `small` can also rarely differ by a word for the same reason; rerun before treating a one-word diff as a regression.

External requirement: **ffmpeg** must be on PATH or installed via `winget install Gyan.FFmpeg`. `buscar_ffmpeg()` also looks in the WinGet Links/Packages folders under `%LOCALAPPDATA%`, because winget installs often aren't on PATH in the current shell.

## Pipeline

`main()` → `normalizar_entrada()` → [`descargar_subtitulos()` if `--subtitulos`] → `descargar_audio()` (skipped for local files or when subtitles were used) → `transcribir()` → `en_parrafos()` → write `.txt` → delete the downloaded audio (unless `--conservar-audio`).

- **Input**: with no `url` arg, the clipboard is read (PowerShell `Get-Clipboard`). `normalizar_entrada` accepts a DevTools "Copy as cURL" (cmd `^` escapes stripped; URL and `-H referer` extracted) and rewrites any YouTube variant (embed, nocookie, shorts, youtu.be, stats pings with `docid=`) to `watch?v=ID`, dropping the referer for YouTube.
- **Subtitles** (`--subtitulos`): only human-made subtitles (`info["subtitles"]`, never `automatic_captions`; Whisper beats YouTube auto-captions). Language = `--idioma`, else the video's language, else the only one available; otherwise it falls back to Whisper. `leer_subtitulos` parses vtt/srt into segment-like objects so they go through the same `en_parrafos`.
- **Vocabulary** (`--vocabulario`): passed as faster-whisper `hotwords`, not `initial_prompt` — with `condition_on_previous_text=False` the prompt only affects the first 30 s window, hotwords apply to every window.

- **Download**: yt-dlp extracts best audio and converts it with ffmpeg to mono 16 kHz 64k mp3 (the format Whisper uses). Output name template is `%(title).80B - %(id)s`, which also becomes the `.txt` name. Auth options for protected streams: `--referer` (also sets `Origin`), `--cookies-navegador`, `--cookies`. 401/403 errors print a Spanish troubleshooting hint and exit.
- **Transcription**: `WhisperModel(device="cpu", compute_type="int8")`, default model `small`. `vad_filter=True` and `condition_on_previous_text=False` are deliberate: they skip silence/music and prevent hallucinated repetition loops. Don't remove them.
- **Paragraphing**: `en_parrafos` is a generator over the lazy segment generator (this is where the actual transcription runs); it starts a new paragraph after a pause > 2 s or after ~600 chars ending in sentence punctuation, and prints progress, speed and ETA every 5 s. `main()` writes and flushes each paragraph as it is yielded, so a crash/Ctrl+C on a multi-hour file keeps the partial `.txt` and the downloaded audio (it prints the command to resume from the local audio).
- **Format selection**: `bestaudio/worst` — for HLS streams with muxed video+audio (e.g. Bunny/mediadelivery) the lowest-resolution variant carries the same audio at a fraction of the size. Don't change it to `best`.
- **Bunny Stream** (`iframe.mediadelivery.net/embed/LIB/ID`, `*.b-cdn.net/.../playlist.m3u8`) is supported by yt-dlp's `bunnycdn` extractor, usually needing the course page as Referer. Its HLS is AES-128 encrypted with segments named `.dts`: `pycryptodomex` must stay installed so yt-dlp decrypts natively — without it yt-dlp delegates to ffmpeg, which rejects the `.dts` extension. Its CDN (`*.b-cdn.net`) chains to SSL.com TLS RSA Root CA 2022, which Windows installs on demand, hence `truststore.inject_into_ssl()` in `main()`. `normalizar_entrada` rejects copied player telemetry requests (`.metrics/track-session`) with instructions on which request to copy.
- `yt_dlp` and `faster_whisper` are imported lazily inside functions so `--help` stays fast.
- Local-file detection: the arg has no `://` and the path exists.
- Paths: `--salida` defaults to `transcripciones/` next to the script (`RAIZ`), not the cwd. The downloaded audio is written into that same folder and deleted afterwards. Whisper models are cached by Hugging Face Hub (first run per model downloads it).
