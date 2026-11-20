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

Ojo: no vale cualquier petición. Las de estadísticas del reproductor (`ptracking`, `stats`, `.metrics/track-session`...) no siempre llevan el vídeo. En YouTube suelen incluir el id y funcionan; en reproductores Bunny (`mediadelivery.net`) no, y la herramienta te dirá que copies la petición a `iframe.mediadelivery.net/embed/NUMERO/ID` (filtra por `embed` en la pestaña Red) o la que acaba en `playlist.m3u8`.

Si el servidor devuelve 401/403, prueba por este orden: `--referer`, `--cookies-navegador` (con el navegador cerrado) y `--cookies`.

## Rendimiento orientativo

En un portátil con CPU y el modelo `small`, un vídeo de 3 minutos tarda alrededor de 1 minuto en total. Durante la transcripción se muestra la velocidad (`x3.0` = 3 minutos de audio por minuto real) y el tiempo restante estimado.

## Transcripciones largas (horas)

- El texto se va guardando párrafo a párrafo. Si se corta (fallo o Ctrl+C), lo transcrito hasta ese momento queda en el `.txt` y el audio descargado se conserva; la herramienta muestra el comando para repetir la transcripción sin volver a descargar (empieza de nuevo desde el principio del audio).
- Si el vídeo no tiene una pista de solo audio, se descarga la versión de menor resolución: el audio es el mismo y pesa mucho menos.
- Deja el portátil enchufado y que no entre en suspensión.

## Consumo de CPU y memoria

- **RAM:** con el modelo `small`, unos 0,75 GB, más unos 230 MB por cada hora de audio. No crece durante la transcripción.
- **CPU:** usa 4 hilos por defecto y se ejecuta con prioridad baja, así que el ordenador sigue respondiendo con normalidad. Que la CPU vaya al 100 % un buen rato no la daña: si se calienta, ella misma baja la velocidad.
- Para ir aún más suave: `--hilos 2` (más lento). En un sobremesa con muchos núcleos, `--hilos 8` puede acelerar.
- `--modelo medium` usa unas 2-3 veces más RAM y tiempo que `small`.

## Seguridad y privacidad

- **Cookies y sesiones:** `--cookies`, `--cookies-navegador` y los `.har` o las peticiones copiadas con «Copiar como cURL» pueden contener sesiones iniciadas. No los subas a ningún sitio ni los pegues en issues. El repositorio ignora `cookies*`, `*.har` y `.env`, pero eso no sustituye a tener cuidado al manejarlos.
- **Contenido descargado:** el audio, los vídeos y las transcripciones se guardan en `transcripciones/`, que está excluida del control de versiones salvo la salida de referencia del smoke test. Revisa antes de compartir una transcripción si tiene datos personales o contenido con copyright.
- **Procesamiento local:** la transcripción se hace en tu equipo. Hugging Face solo sirve para descargar los modelos la primera vez.
- **Vulnerabilidades:** repórtalas en privado según [SECURITY.md](SECURITY.md), nunca como issue público.

## Contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para preparar el entorno, ejecutar el smoke test y abrir un pull request. Todos debemos seguir el [código de conducta](CODE_OF_CONDUCT.md).

## Licencia

Distribuido bajo la [GNU General Public License v3.0](LICENSE) (GPLv3). Puedes usarlo, estudiarlo, modificarlo y redistribuirlo bajo esos términos. Las dependencias usan licencias compatibles (MIT, BSD, Apache-2.0, Unlicense); ffmpeg se instala aparte y no forma parte del repositorio.

Copyright (C) [YEAR] [HOLDER]
