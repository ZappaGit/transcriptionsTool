# Contributing

Thanks for your interest. Before you start, please read the [Code of Conduct](CODE_OF_CONDUCT.md) and the [security policy](SECURITY.md).

## Setting up the environment

Requirements: [uv](https://docs.astral.sh/uv/) and ffmpeg. On Windows: `winget install Gyan.FFmpeg`. On Linux or WSL: `sudo apt install ffmpeg`.

Windows (PowerShell):

```powershell
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
uv run python transcribir.py --help
```

Linux and WSL (bash):

```bash
git clone https://github.com/ZappaGit/transcriptionsTool.git
cd transcriptionsTool
uv sync
uv run python transcribir.py --help
```

## Checks

The project has no unit tests. The reference check is the smoke test: a short 19-second YouTube video whose output must match the reference version stored in `transcripciones/`:

```powershell
uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --salida $env:TEMP\humo
```

On Linux or WSL:

```bash
uv run python transcribir.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --salida /tmp/humo
```

Compare the resulting `.txt` with `transcripciones/Me at the zoo - jNQXAC9IVRw.txt`.

Notes:

- Use the default model (`small`). With `tiny`, the output changes between runs because Whisper samples again in low-confidence windows.
- With `small`, a single word may occasionally change for the same reason. Run the test again before accepting a one-word difference.

## Conventions

- The code, comments, command-line options and user-facing messages are in **Spanish**. Please keep them that way.
- Read [CLAUDE.md](CLAUDE.md): it describes the architecture and the decisions that should not be reverted. In particular:
  - `vad_filter=True` and `condition_on_previous_text=False` are deliberate; do not remove them.
  - The `bestaudio/worst` format selection must not be changed to `best`.
  - YouTube's automatic captions are not used (only human-made subtitles).
- Keep dependencies to a minimum. If you add one, explain why in the pull request description and check that its license is compatible with GPLv3.
- Do not add audio, video, transcripts, cookies, tokens, models or personal paths to the repository. They are excluded in `.gitignore`. If you need a new reference output, discuss it in an issue first.

## Opening a pull request

1. Create a branch from `main` (do not work directly on `main`).
2. Keep changes small and focused. One PR per topic.
3. Run the smoke test and `--help`, and note the results in the PR template.
4. Open the PR against `main` and fill in the [pull request template](.github/pull_request_template.md).
5. A maintainer will review the PR. The CodeQL checks must pass before merging.

## Licensing of contributions

The project is distributed under the [GPLv3](LICENSE). By submitting a contribution you agree that it will be published under the same license. Keep the SPDX header in new files:

```python
# SPDX-License-Identifier: GPL-3.0-or-later
```

## Reporting problems

- Bugs and feature requests: open an issue using the matching template.
- Security vulnerabilities: do **not** open an issue. Follow [SECURITY.md](SECURITY.md).
