"""Descarga el audio de una URL (YouTube, .m3u8, etc.) y lo transcribe a .txt.

Uso:
    transcribir URL
    transcribir URL --modelo medium --idioma es
    transcribir URL --referer https://sitio.com/pagina --cookies-navegador chrome
    transcribir C:\\ruta\\audio.mp3          (también acepta archivos locales)
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Silencia avisos inofensivos de la caché de modelos en Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def buscar_ffmpeg() -> str | None:
    """Devuelve la carpeta donde está ffmpeg (PATH o instalación de winget)."""
    exe = shutil.which("ffmpeg")
    if exe:
        return str(Path(exe).resolve().parent)
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    enlace = local / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
    if enlace.exists():
        return str(enlace.resolve().parent)
    for exe in (local / "Microsoft" / "WinGet" / "Packages").glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"):
        return str(exe.parent)
    return None


def descargar_audio(url: str, carpeta: Path, args) -> tuple[Path, str]:
    """Baja solo el audio y lo deja en mono 16 kHz (lo que usa Whisper)."""
    import yt_dlp

    ffmpeg = buscar_ffmpeg()
    if not ffmpeg:
        sys.exit("No encuentro ffmpeg. Instálalo con: winget install Gyan.FFmpeg")

    opciones = {
        "format": "bestaudio/best",
        "outtmpl": str(carpeta / "%(title).80B - %(id)s.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": True,
        "ffmpeg_location": ffmpeg,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "64"}],
        "postprocessor_args": {"extractaudio": ["-ac", "1", "-ar", "16000"]},
    }
    if args.referer:
        origen = "/".join(args.referer.split("/")[:3])
        opciones["http_headers"] = {"Referer": args.referer, "Origin": origen}
    if args.cookies_navegador:
        opciones["cookiesfrombrowser"] = (args.cookies_navegador,)
    if args.cookies:
        opciones["cookiefile"] = args.cookies

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        texto = str(e)
        if "403" in texto or "401" in texto or "Forbidden" in texto:
            print(
                "\nEl servidor rechazó la descarga (enlace protegido). Prueba, por este orden:\n"
                "  1) --referer URL_DE_LA_PAGINA_DONDE_SE_VE_EL_VIDEO\n"
                "  2) --cookies-navegador firefox   (o chrome / edge, con el navegador cerrado)\n"
                "  3) --cookies cookies.txt         (exportadas con una extensión tipo 'Get cookies.txt LOCALLY')\n"
                "  Si el .m3u8 lleva un token que caduca, cópialo de nuevo y lánzalo enseguida.",
                file=sys.stderr,
            )
        sys.exit(1)

    audio = Path(info["requested_downloads"][0]["filepath"])
    return audio, audio.stem


def en_parrafos(segmentos, duracion: float) -> str:
    """Une los segmentos en párrafos: corta en pausas largas o al acumular texto."""
    parrafos, actual, fin_anterior = [], [], 0.0
    ultimo_aviso = time.time()
    for seg in segmentos:
        texto = seg.text.strip()
        if not texto:
            continue
        largo = sum(len(t) + 1 for t in actual)
        pausa = seg.start - fin_anterior
        if actual and (pausa > 2.0 or (largo > 600 and actual[-1][-1:] in ".?!…")):
            parrafos.append(" ".join(actual))
            actual = []
        actual.append(texto)
        fin_anterior = seg.end
        if duracion and time.time() - ultimo_aviso > 5:
            print(f"  {seg.end / duracion:5.1%}  ({seg.end / 60:.1f} de {duracion / 60:.1f} min)", flush=True)
            ultimo_aviso = time.time()
    if actual:
        parrafos.append(" ".join(actual))
    return "\n\n".join(parrafos) + "\n"


def transcribir(audio: Path, args) -> str:
    from faster_whisper import WhisperModel

    print(f"Cargando modelo '{args.modelo}' (la primera vez se descarga)...", flush=True)
    modelo = WhisperModel(
        args.modelo,
        device="cpu",
        compute_type="int8",
        cpu_threads=min(8, os.cpu_count() or 4),
    )
    segmentos, info = modelo.transcribe(
        str(audio),
        language=args.idioma,
        beam_size=5,
        vad_filter=True,  # salta silencios y música: más rápido y sin texto inventado
        condition_on_previous_text=False,  # evita bucles de frases repetidas
    )
    print(f"Idioma: {info.language} | Duración: {info.duration / 60:.1f} min. Transcribiendo...", flush=True)
    return en_parrafos(segmentos, info.duration)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="URL de vídeo/audio -> transcripción .txt")
    p.add_argument("url", help="URL (YouTube, .m3u8, etc.) o ruta a un archivo local")
    p.add_argument("--modelo", default="small",
                   help="tiny, base, small (por defecto), medium, large-v3-turbo. Más grande = más preciso y más lento")
    p.add_argument("--idioma", default=None, help="Código de idioma (es, en...). Por defecto se detecta solo")
    p.add_argument("--salida", default=str(RAIZ / "transcripciones"), help="Carpeta de salida")
    p.add_argument("--referer", help="Página donde se reproduce el vídeo (arregla muchos 403 en .m3u8)")
    p.add_argument("--cookies-navegador", help="Usar cookies de: chrome, edge, firefox...")
    p.add_argument("--cookies", help="Archivo cookies.txt (formato Netscape)")
    p.add_argument("--conservar-audio", action="store_true", help="No borrar el audio descargado")
    args = p.parse_args()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    inicio = time.time()

    local = Path(args.url)
    es_local = "://" not in args.url and local.exists()
    if es_local:
        audio, nombre = local, local.stem
    else:
        audio, nombre = descargar_audio(args.url, salida, args)
        print(f"Audio: {audio.name}", flush=True)

    texto = transcribir(audio, args)
    destino = salida / f"{nombre}.txt"
    destino.write_text(texto, encoding="utf-8")

    if not es_local and not args.conservar_audio:
        audio.unlink(missing_ok=True)

    print(f"\nListo en {(time.time() - inicio) / 60:.1f} min -> {destino}")


if __name__ == "__main__":
    main()
