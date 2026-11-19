# transcribir

Herramienta de línea de comandos para Windows que descarga el audio de un vídeo (YouTube, streams `.m3u8` y [todo lo que soporta yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) o toma un archivo de audio local, lo transcribe con [faster-whisper](https://github.com/SYSTRAN/faster-whisper) en la CPU y guarda el texto en párrafos en un `.txt`.

Todo funciona en local: no se envía el audio a ningún servicio externo.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala Python ≥ 3.12 y las dependencias)
- **ffmpeg**: `winget install Gyan.FFmpeg` (no hace falta que esté en el PATH; se busca también en la carpeta de winget)
- Recomendado: **Deno** (`winget install DenoLand.Deno`), que yt-dlp necesita para extraer bien los vídeos de YouTube

## Instalación

```powershell
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
```

La primera vez que se usa cada modelo de Whisper se descarga automáticamente (de decenas de MB para `tiny` a más de 1 GB para los grandes).

## Uso

```powershell
.\transcribir.cmd URL                                   # funciona desde cualquier carpeta
.\transcribir.cmd URL --modelo medium --idioma es
.\transcribir.cmd C:\ruta\audio.mp3                     # archivo local, sin descarga
.\transcribir.cmd URL --vocabulario "Claude, Claude Code, Anthropic"
.\transcribir.cmd URL --subtitulos                      # usa los subtítulos del vídeo si los hay
.\transcribir.cmd                                       # sin URL: la lee del portapapeles
```

También se puede lanzar con `uv run python transcribir.py ...`.

El resultado se guarda en `transcripciones\<título> - <id>.txt`. El audio descargado se borra al terminar (salvo con `--conservar-audio`).

### Opciones

| Opción | Descripción |
|---|---|
| `--modelo` | `tiny`, `base`, `small` (por defecto), `medium`, `large-v3-turbo`. Más grande = más preciso y más lento |
| `--idioma` | Código de idioma (`es`, `en`...). Por defecto se detecta solo |
| `--vocabulario` | Nombres propios o términos técnicos que Whisper suele escribir mal |
| `--subtitulos` | Si el vídeo tiene subtítulos hechos por personas, se usan en vez de transcribir (instantáneo). Si no, transcribe con Whisper |
| `--salida` | Carpeta de salida (por defecto `transcripciones` junto al script) |
| `--referer` | Página donde se reproduce el vídeo (arregla muchos errores 403 en `.m3u8`) |
| `--cookies-navegador` | Usar las cookies de `chrome`, `edge`, `firefox`... |
| `--cookies` | Archivo `cookies.txt` en formato Netscape |
| `--conservar-audio` | No borrar el audio descargado |

## Vídeos incrustados en otras webs

Cuando el vídeo está dentro de otra página (un curso, una web con reproductor propio), la forma más fácil es:

1. Abre las DevTools del navegador (F12) → pestaña **Red** y reproduce el vídeo.
2. Haz clic derecho en una petición del vídeo → **Copiar** → **Copiar como cURL (cmd)**.
3. Ejecuta `.\transcribir.cmd` sin argumentos.

La herramienta lee el portapapeles, saca la URL y el Referer del cURL y, si es un vídeo de YouTube incrustado, lo convierte en la URL normal del vídeo. Para streams `.m3u8` busca la petición que acaba en `.m3u8`; si lleva un token que caduca, lánzalo enseguida.

Si el servidor devuelve 401/403, prueba por este orden: `--referer`, `--cookies-navegador` (con el navegador cerrado) y `--cookies`.

## Rendimiento orientativo

En un portátil con CPU y el modelo `small`, un vídeo de 3 minutos tarda alrededor de 1 minuto en total.
