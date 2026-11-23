# 🎧 transcribir

**From a video or audio file to a paragraphed transcript, fully local and CPU-only.**

transcribir downloads the audio of a video (YouTube, `.m3u8` streams, and [anything yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) or takes a local audio file, transcribes it with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) on the CPU, and writes the text in paragraphs to a `.txt` file. Nothing is sent to an external service: the audio never leaves your machine.

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![license GPLv3](https://img.shields.io/badge/license-GPLv3-blue)
![GPU not required](https://img.shields.io/badge/GPU-not%20required-orange)

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Options](#options)
- [Embedded videos on other websites](#embedded-videos-on-other-websites)
- [Performance](#performance)
- [Long transcriptions (hours)](#long-transcriptions-hours)
- [CPU and memory use](#cpu-and-memory-use)
- [Security and privacy](#security-and-privacy)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 and the dependencies; the version is pinned in `.python-version`)
- **ffmpeg**:
  - Windows: `winget install Gyan.FFmpeg` (it does not need to be on the PATH; the winget folder is searched too)
  - Linux / WSL: `sudo apt install ffmpeg`
- Recommended: **Deno** (`winget install DenoLand.Deno` on Windows; see [deno.land](https://deno.land) on Linux), which yt-dlp needs to extract YouTube videos properly
- Clipboard mode (no URL argument) on Linux needs `wl-clipboard` (Wayland) or `xclip` (X11). Under WSL it uses the Windows clipboard automatically.

## Installation

Windows (PowerShell):

```powershell
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
```

Linux and WSL (bash):

```bash
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
chmod +x transcribir.sh   # only if git did not keep the execute bit
```

The first time each Whisper model is used, it is downloaded automatically (from tens of MB for `tiny` to more than 1 GB for the large ones).

## Usage

Windows:

```powershell
.\transcribir.cmd URL                                   # works from any folder
.\transcribir.cmd URL --modelo medium --idioma es
.\transcribir.cmd C:\ruta\audio.mp3                     # local file, no download
.\transcribir.cmd URL --vocabulario "Claude, Claude Code, Anthropic"
.\transcribir.cmd URL --subtitulos                      # uses the video's subtitles if it has them
.\transcribir.cmd                                       # no URL: reads it from the clipboard
```

Linux and WSL: the same options with the wrapper `./transcribir.sh`, and paths in Linux format:

```bash
./transcribir.sh URL
./transcribir.sh URL --modelo medium --idioma es
./transcribir.sh /ruta/audio.mp3
```

You can also run it with `uv run python transcribir.py ...` on any platform.

The result is saved as `transcripciones\<title> - <id>.txt`. The downloaded audio is deleted when it finishes (unless you use `--conservar-audio`).

> Note: the command-line options and the program's messages are in Spanish (`--modelo`, `--idioma`, `--salida`...). Use them as shown here.

## Options

| Option | Description |
|---|---|
| `--modelo` | `tiny`, `base`, `small` (default), `medium`, `large-v3-turbo`. Larger = more accurate and slower |
| `--idioma` | Language code (`es`, `en`...). Detected automatically by default |
| `--vocabulario` | Proper names or technical terms that Whisper tends to get wrong |
| `--subtitulos` | If the video has human-made subtitles, they are used instead of transcribing (instant). Otherwise it transcribes with Whisper |
| `--salida` | Output folder (default: `transcripciones` next to the script) |
| `--referer` | Page where the video is played (fixes many 403 errors on `.m3u8`) |
| `--cookies-navegador` | Use the cookies of `chrome`, `edge`, `firefox`... |
| `--cookies` | `cookies.txt` file in Netscape format |
| `--conservar-audio` | Do not delete the downloaded audio |
| `--hilos` | Number of CPU threads (default: 4) |
| `--prioridad-normal` | Do not lower the process priority |

## Embedded videos on other websites

When the video is inside another page (a course, a site with its own player), the easiest way is:

1. Open the browser's DevTools (F12) → **Network** tab and play the video.
2. Right-click a video request → **Copy** → **Copy as cURL (cmd)**.
3. Run `.\transcribir.cmd` with no arguments.

The tool reads the clipboard, extracts the URL and the Referer from the cURL and, if it is an embedded YouTube video, converts it to the normal video URL. For `.m3u8` streams it looks for the request that ends in `.m3u8`; if it carries a token that expires, run it right away.

Be careful: not every request works. Player statistics requests (`ptracking`, `stats`, `.metrics/track-session`...) do not always contain the video. On YouTube they usually include the id and work; on Bunny players (`mediadelivery.net`) they do not, and the tool will tell you to copy the request to `iframe.mediadelivery.net/embed/NUMBER/ID` (filter by `embed` in the Network tab) or the one that ends in `playlist.m3u8`.

If the server returns 401/403, try in this order: `--referer`, `--cookies-navegador` (with the browser closed) and `--cookies`.

## Performance

On a laptop CPU with the `small` model, a 3-minute video takes about 1 minute in total. During transcription the speed is shown (`x3.0` = 3 minutes of audio per real minute) along with the estimated time remaining.

## Long transcriptions (hours)

- The text is saved paragraph by paragraph. If it stops (failure or Ctrl+C), what was transcribed up to that point stays in the `.txt`, and the downloaded audio is kept; the tool shows the command to repeat the transcription without downloading again (it starts again from the beginning of the audio).
- If the video has no audio-only track, the lowest-resolution version is downloaded: the audio is the same and much smaller.
- Keep the laptop plugged in and prevent it from going to sleep.

## CPU and memory use

- **RAM:** with the `small` model, about 0.75 GB, plus about 230 MB per hour of audio. It does not grow during transcription.
- **CPU:** uses 4 threads by default and runs with low priority, so the computer stays responsive. Keeping the CPU at 100 % for a long time does not damage it: if it heats up, it slows itself down.
- To go even lighter: `--hilos 2` (slower). On a desktop with many cores, `--hilos 8` may be faster.
- `--modelo medium` uses about 2–3 times more RAM and time than `small`.

## Security and privacy

- **Cookies and sessions:** `--cookies`, `--cookies-navegador`, and `.har` files or requests copied with "Copy as cURL" can contain logged-in sessions. Do not upload them anywhere or paste them into issues. The repository ignores `cookies*`, `*.har` and `.env`, but that does not replace being careful with them.
- **Downloaded content:** audio, videos and transcripts are saved in `transcripciones/`, which is excluded from version control except for the smoke-test reference output. Check a transcript for personal data or copyrighted content before sharing it.
- **Local processing:** transcription happens on your machine. Hugging Face is only used to download the models the first time.
- **Vulnerabilities:** report them privately following [SECURITY.md](SECURITY.md), never as a public issue.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) to set up the environment, run the smoke test and open a pull request. Everyone is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Distributed under the [GNU General Public License v3.0](LICENSE) (GPLv3). You may use, study, modify and redistribute it under those terms. The dependencies use compatible licenses (MIT, BSD, Apache-2.0, Unlicense); ffmpeg is installed separately and is not part of the repository.

Copyright (C) 2026 Diego Izquierdo Fernandez
