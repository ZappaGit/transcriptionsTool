# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) [YEAR] [HOLDER]
"""Descarga el audio de una URL (YouTube, .m3u8, etc.) y lo transcribe a .txt.

Uso:
    transcribir URL
    transcribir URL --modelo medium --idioma es
    transcribir URL --referer https://sitio.com/pagina --cookies-navegador chrome
    transcribir C:\\ruta\\audio.mp3          (también acepta archivos locales)
    transcribir URL --vocabulario "Claude, Claude Code, Anthropic"
    transcribir URL --subtitulos            (usa los subtítulos humanos si los hay)
    transcribir                             (lee la URL o un "Copiar como cURL" del portapapeles)
"""

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

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


HOSTS_YOUTUBE = ("youtube.com", "youtube-nocookie.com", "youtu.be")


def leer_portapapeles() -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout.strip()


def normalizar_entrada(texto: str, args) -> str:
    """Acepta URL normal, embed, o un 'Copiar como cURL' de las DevTools.

    De un cURL saca la URL (y el Referer si no se dio --referer). Las URLs de
    YouTube (embed, nocookie, pings de estadísticas con docid=) se convierten
    en la URL normal del vídeo.
    """
    original = texto.strip()
    url = original
    es_curl = url.lower().startswith("curl")
    if es_curl:
        limpio = url.replace("^", "")  # escapes de cmd ("Copiar como cURL (cmd)")
        m = re.search(r"https?://[^\s'\"]+", limpio)
        if not m:
            sys.exit("No encuentro ninguna URL dentro del cURL pegado.")
        url = m.group(0)
        ref = re.search(r"""-H\s+['"]referer:\s*([^'"]+)['"]""", limpio, re.IGNORECASE)
        if ref and not args.referer:
            args.referer = ref.group(1).strip()

    partes = urlparse(url)
    host = partes.hostname or ""
    if "mediadelivery.net" in host or "b-cdn.net" in host or "bunnycdn" in host:
        es_video = re.search(r"/(embed|play)/\d+/[\da-f-]+|\.m3u8", partes.path)
        if not es_video:
            sys.exit(
                "Esa petición no es el vídeo (es de estadísticas del reproductor Bunny/mediadelivery).\n"
                "En la pestaña Red de las DevTools filtra por 'embed' y copia como cURL la petición a\n"
                "  iframe.mediadelivery.net/embed/NUMERO/ID   (o la que acaba en playlist.m3u8)\n"
                "y vuelve a ejecutar transcribir."
            )
    if any(host == h or host.endswith("." + h) for h in HOSTS_YOUTUBE):
        args.referer = None  # no hace falta para YouTube y a veces estorba
        q = parse_qs(partes.query)
        video_id = (q.get("docid") or q.get("video_id") or q.get("v") or [None])[0]
        m = re.match(r"/(?:embed|shorts|live|v)/([\w-]{11})", partes.path)
        if not video_id and m:
            video_id = m.group(1)
        if not video_id and host == "youtu.be":
            video_id = partes.path.strip("/")[:11] or None
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
        elif "/api/" in partes.path:
            sys.exit("Esa petición de YouTube no lleva el id del vídeo. Copia la URL de la página del vídeo.")
    elif "googlevideo.com" in host:
        print("Aviso: las URLs de googlevideo.com caducan enseguida; mejor usa la URL del vídeo.", file=sys.stderr)

    if url != original:
        print(f"URL detectada: {url}" + (f"  (referer: {args.referer})" if args.referer else ""), flush=True)
    return url


def opciones_ytdlp(carpeta: Path, args) -> dict:
    from yt_dlp.postprocessor.metadataparser import MetadataParserPP

    opciones = {
        "outtmpl": str(carpeta / "%(title).80B - %(id)s.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        # Algunos sitios (p. ej. Bunny) usan el nombre del archivo subido como título:
        # "Clase 3.mp4" -> "Clase 3", para que no acabe en "Clase 3.mp4 - id.txt".
        "postprocessors": [{
            "key": "MetadataParser",
            "when": "pre_process",
            "actions": [(MetadataParserPP.Actions.REPLACE, "title",
                         r"(?i)\.(mp4|m4v|mkv|webm|mov|avi|mp3|m4a|wav)$", "")],
        }],
    }
    if args.referer:
        origen = "/".join(args.referer.split("/")[:3])
        opciones["http_headers"] = {"Referer": args.referer, "Origin": origen}
    if args.cookies_navegador:
        opciones["cookiesfrombrowser"] = (args.cookies_navegador,)
    if args.cookies:
        opciones["cookiefile"] = args.cookies
    return opciones


def elegir_idioma(disponibles: list[str], preferido: str | None) -> str | None:
    """'es' coincide con 'es', 'es-ES', 'es-419'..."""
    if not preferido:
        return None
    preferido = preferido.lower()
    for clave in disponibles:
        if clave.lower() == preferido:
            return clave
    for clave in disponibles:
        if clave.lower().split("-")[0] == preferido.split("-")[0]:
            return clave
    return None


def a_segundos(marca: str) -> float:
    partes = marca.replace(",", ".").split(":")
    return sum(float(p) * 60 ** i for i, p in enumerate(reversed(partes)))


def leer_subtitulos(ruta: Path) -> list:
    """Parsea .vtt / .srt en segmentos (start, end, text), quitando duplicados."""
    bloques = re.split(r"\n\s*\n", ruta.read_text(encoding="utf-8", errors="replace").replace("\r", ""))
    segmentos, anterior = [], None
    for bloque in bloques:
        lineas = bloque.strip().split("\n")
        for i, linea in enumerate(lineas):
            m = re.match(r"([\d:.,]+)\s*-->\s*([\d:.,]+)", linea)
            if m:
                texto = " ".join(lineas[i + 1:])
                texto = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", texto))).strip()
                if texto and texto != anterior:
                    segmentos.append(SimpleNamespace(start=a_segundos(m.group(1)), end=a_segundos(m.group(2)), text=texto))
                    anterior = texto
                break
    return segmentos


def descargar_subtitulos(url: str, carpeta: Path, args) -> tuple[str, str] | None:
    """Si el vídeo tiene subtítulos hechos por personas, los devuelve como texto."""
    import yt_dlp

    opciones = opciones_ytdlp(carpeta, args) | {"skip_download": True, "quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError:
        return None  # ya fallará (con su mensaje) al bajar el audio

    disponibles = [k for k in (info.get("subtitles") or {}) if k != "live_chat"]
    if not disponibles:
        print("No hay subtítulos hechos por personas; se transcribe con Whisper.", flush=True)
        return None
    idioma = elegir_idioma(disponibles, args.idioma) or elegir_idioma(disponibles, info.get("language"))
    if not idioma and len(disponibles) == 1:
        idioma = disponibles[0]
    if not idioma:
        print(f"Hay subtítulos en: {', '.join(disponibles)}. Elige uno con --idioma. "
              "Se transcribe con Whisper.", flush=True)
        return None

    opciones |= {"writesubtitles": True, "subtitleslangs": [idioma], "subtitlesformat": "vtt/srt/best"}
    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.process_ie_result(info, download=True)
    ruta = Path(info["requested_subtitles"][idioma]["filepath"])
    segmentos = leer_subtitulos(ruta)
    ruta.unlink(missing_ok=True)
    if not segmentos:
        print("Los subtítulos están vacíos o en un formato que no entiendo; se transcribe con Whisper.", flush=True)
        return None
    print(f"Usando subtítulos '{idioma}' del vídeo (sin Whisper).", flush=True)
    nombre = Path(ydl.prepare_filename(info)).stem
    return list(en_parrafos(segmentos, 0)), nombre


def descargar_audio(url: str, carpeta: Path, args) -> tuple[Path, str]:
    """Baja solo el audio y lo deja en mono 16 kHz (lo que usa Whisper)."""
    import yt_dlp

    ffmpeg = buscar_ffmpeg()
    if not ffmpeg:
        sys.exit("No encuentro ffmpeg. Instálalo con: winget install Gyan.FFmpeg")

    opciones = opciones_ytdlp(carpeta, args)
    opciones["postprocessors"] += [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "64"},
    ]
    opciones |= {
        # Si no hay pista de solo audio (HLS con vídeo+audio juntos), la variante de
        # menor resolución trae el mismo audio y pesa mucho menos que la de 1080p.
        "format": "bestaudio/worst",
        "ffmpeg_location": ffmpeg,
        "concurrent_fragment_downloads": 4,
        "postprocessor_args": {"extractaudio": ["-ac", "1", "-ar", "16000"]},
    }

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


def en_parrafos(segmentos, duracion: float):
    """Genera párrafos: corta en pausas largas o al acumular texto.

    Es un generador para poder escribir cada párrafo en cuanto se cierra: en una
    transcripción de horas, un fallo o Ctrl+C no se lleva por delante lo ya hecho.
    """
    actual, fin_anterior = [], 0.0
    inicio = ultimo_aviso = time.time()
    for seg in segmentos:
        texto = seg.text.strip()
        if not texto:
            continue
        largo = sum(len(t) + 1 for t in actual)
        pausa = seg.start - fin_anterior
        if actual and (pausa > 2.0 or (largo > 600 and actual[-1][-1:] in ".?!…")):
            yield " ".join(actual)
            actual = []
        actual.append(texto)
        fin_anterior = seg.end
        if duracion and time.time() - ultimo_aviso > 5:
            ultimo_aviso = time.time()
            velocidad = seg.end / max(ultimo_aviso - inicio, 1e-6)  # segundos de audio por segundo real
            quedan = (duracion - seg.end) / velocidad / 60 if velocidad else 0
            print(f"  {seg.end / duracion:5.1%}  ({seg.end / 60:.1f} de {duracion / 60:.1f} min)"
                  f"  x{velocidad:.1f}  quedan ~{quedan:.0f} min", flush=True)
    if actual:
        yield " ".join(actual)


def transcribir(audio: Path, args):
    from faster_whisper import WhisperModel

    print(f"Cargando modelo '{args.modelo}' (la primera vez se descarga)...", flush=True)
    modelo = WhisperModel(
        args.modelo,
        device="cpu",
        compute_type="int8",
        cpu_threads=args.hilos,
    )
    segmentos, info = modelo.transcribe(
        str(audio),
        language=args.idioma,
        beam_size=5,
        vad_filter=True,  # salta silencios y música: más rápido y sin texto inventado
        condition_on_previous_text=False,  # evita bucles de frases repetidas
        # hotwords se aplica a cada ventana de 30 s; initial_prompt solo a la primera
        # porque condition_on_previous_text=False reinicia el contexto.
        hotwords=args.vocabulario,
    )
    print(f"Idioma: {info.language} | Duración: {info.duration / 60:.1f} min. Transcribiendo...", flush=True)
    return en_parrafos(segmentos, info.duration)


def bajar_prioridad():
    """Prioridad 'por debajo de lo normal': el PC sigue respondiendo mientras transcribe.

    No ralentiza la transcripción si no hay otra cosa pidiendo CPU. Los procesos hijos
    (ffmpeg) heredan la prioridad.
    """
    if sys.platform == "win32":
        import ctypes
        BELOW_NORMAL_PRIORITY_CLASS = 0x4000
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        k32.SetPriorityClass(ctypes.c_void_p(k32.GetCurrentProcess()), BELOW_NORMAL_PRIORITY_CLASS)


def main():
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="URL de vídeo/audio -> transcripción .txt")
    p.add_argument("url", nargs="?",
                   help="URL (YouTube, .m3u8, embed, 'Copiar como cURL'...) o ruta a un archivo local. "
                        "Si se omite, se lee del portapapeles")
    p.add_argument("--modelo", default="small",
                   help="tiny, base, small (por defecto), medium, large-v3-turbo. Más grande = más preciso y más lento")
    p.add_argument("--idioma", default=None, help="Código de idioma (es, en...). Por defecto se detecta solo")
    p.add_argument("--salida", default=str(RAIZ / "transcripciones"), help="Carpeta de salida")
    p.add_argument("--referer", help="Página donde se reproduce el vídeo (arregla muchos 403 en .m3u8)")
    p.add_argument("--cookies-navegador", help="Usar cookies de: chrome, edge, firefox...")
    p.add_argument("--cookies", help="Archivo cookies.txt (formato Netscape)")
    p.add_argument("--conservar-audio", action="store_true", help="No borrar el audio descargado")
    p.add_argument("--vocabulario",
                   help='Nombres o términos que Whisper debe reconocer, p. ej. "Claude, Claude Code, Anthropic"')
    p.add_argument("--hilos", type=int, default=min(4, os.cpu_count() or 4),
                   help="Hilos de CPU para Whisper (por defecto 4). En portátiles más hilos apenas "
                        "acelera y calienta más")
    p.add_argument("--prioridad-normal", action="store_true",
                   help="No bajar la prioridad del proceso (por defecto baja, para que el PC siga fluido)")
    p.add_argument("--subtitulos", action="store_true",
                   help="Si el vídeo tiene subtítulos hechos por personas, usarlos en vez de transcribir")
    args = p.parse_args()

    # Verificar HTTPS con el almacén de certificados de Windows (como el navegador).
    # Sin esto, CDNs con raíces recientes (p. ej. *.b-cdn.net de Bunny, SSL.com Root 2022)
    # fallan con CERTIFICATE_VERIFY_FAILED porque Windows solo instala esas raíces bajo demanda.
    import truststore
    truststore.inject_into_ssl()

    if not args.prioridad_normal:
        bajar_prioridad()

    if not args.url:
        args.url = leer_portapapeles()
        if not args.url:
            p.error("falta la URL (y el portapapeles está vacío)")
        print(f"Leído del portapapeles: {args.url[:100]}{'...' if len(args.url) > 100 else ''}", flush=True)

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    inicio = time.time()

    local = Path(args.url)
    es_local = "://" not in args.url and local.exists()
    texto, audio = None, None
    if es_local:
        audio, nombre = local, local.stem
    else:
        args.url = normalizar_entrada(args.url, args)
        if args.subtitulos:
            resultado = descargar_subtitulos(args.url, salida, args)
            if resultado:
                texto, nombre = resultado
        if texto is None:
            audio, nombre = descargar_audio(args.url, salida, args)
            print(f"Audio: {audio.name}", flush=True)

    if texto is None:
        texto = transcribir(audio, args)
    destino = salida / f"{nombre}.txt"
    try:
        with destino.open("w", encoding="utf-8") as f:
            for i, parrafo in enumerate(texto):
                f.write(("\n\n" if i else "") + parrafo)
                f.flush()
            f.write("\n")
    except (KeyboardInterrupt, Exception) as e:
        motivo = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        print(f"\nInterrumpido ({motivo}). Lo transcrito hasta ahora está en: {destino}", file=sys.stderr)
        if audio is not None and not es_local:
            print(f"El audio se conserva; para no volver a descargarlo: transcribir \"{audio}\"", file=sys.stderr)
        sys.exit(1)

    if audio is not None and not es_local and not args.conservar_audio:
        audio.unlink(missing_ok=True)

    print(f"\nListo en {(time.time() - inicio) / 60:.1f} min -> {destino}")


if __name__ == "__main__":
    main()
