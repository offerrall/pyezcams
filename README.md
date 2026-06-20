# pyezcams

**v0.1.1** · [PyPI](https://pypi.org/project/pyezcams/)

Minimal (stdlib-only) toolkit to run a node that captures USB webcams and
streams them over RTSP/WebRTC via [MediaMTX](https://github.com/bluenviron/mediamtx).
A single command (`pyezcams`) starts MediaMTX and one `ffmpeg` per camera and
keeps them alive.

No Python dependencies. Relies on three system binaries: `ffmpeg`, `v4l2-ctl`
and `mediamtx`. Linux only (v4l2 capture).

**Stateless**: the library stores nothing and assumes no paths. All configuration
is the match file, passed explicitly and required.

## Prerequisites

| Binary      | Install                                      |
|-------------|----------------------------------------------|
| `ffmpeg`    | `sudo apt install ffmpeg`                     |
| `v4l2-ctl`  | `sudo apt install v4l-utils`                 |
| `mediamtx`  | binary from [releases](https://github.com/bluenviron/mediamtx/releases) onto the `PATH` |

`check_prerequisites()` verifies them at startup and, if any is missing, says what
to do.

## Install

```bash
pip install pyezcams
```

## Usage

```bash
pyezcams --config cameras.txt                       # defaults: 720p30
pyezcams --config cameras.txt --resolution 1920x1080 --fps 25
```

`--config` is required (no default path). The command checks prerequisites,
detects the encoder, starts MediaMTX and launches one `ffmpeg` per camera,
supervising them (relaunches any that die, clean shutdown on SIGINT/SIGTERM).

### Defaults

Fixed 720p30 surveillance standard; everything works with no flags. Only
`--config` is required; `--resolution` and `--fps` are optional overrides.

| Parameter    | Default              | Applies to              |
|--------------|----------------------|-------------------------|
| resolution   | `1280x720`           | capture (both cases)    |
| framerate    | `30`                 | capture (both cases)    |
| bitrate      | `4M`                 | re-encode (MJPG) only   |
| GOP          | `60` (2s @30fps)     | re-encode (MJPG) only   |
| RTSP output  | `rtsp://localhost:8554/<alias>` | both cases   |

Per case:
- **H264 (copy)** — captures at resolution/fps and copies the native stream
  (`-c:v copy`, ~0 CPU). Bitrate does not apply (nothing is re-encoded).
- **MJPG (re-encode)** — captures at resolution/fps and re-encodes with the
  detected encoder at the given bitrate.

Bitrate and RTSP base are module constants in `command.py`; `build_command`
also takes `video_size`, `framerate` and `bitrate` keyword args for per-camera
overrides.

## Match file

One camera per line, `path = alias` (blank lines and `#` comments ignored):

```
/dev/v4l/by-path/...-video-index0 = laser20w
/dev/v4l/by-path/...-video-index0 = cnc_a
```

Get the paths with `ls -l /dev/v4l/by-path/`.

## API

```python
from pyezcams import (
    parse_match, check_prerequisites, detect_encoder,
    detect_format, build_command, run,
)
```

- **`parse_match(path) -> dict`** — read the match file into `{alias: usb_path}`.
- **`check_prerequisites() -> None`** — verify the three binaries; `RuntimeError`
  if any is missing.
- **`detect_encoder() -> str | None`** — first H.264 encoder that passes a real
  1-frame test (`h264_nvenc > h264_qsv > h264_vaapi > h264_v4l2m2m > libx264`).
  Hang-proof: each test is capped by `ENCODER_TEST_TIMEOUT` (10s). A hardware
  encoder that hangs (broken driver/firmware) is discarded on timeout and the
  detection falls through to the next candidate instead of blocking node
  startup; software `libx264` always works as the final fallback.
- **`detect_format(usb_path) -> str | None`** — `"H264"` (copy) or `"MJPG"`
  (re-encode), or `None`.
- **`build_command(usb_path, alias, fmt, encoder, video_size=..., framerate=..., bitrate=...) -> list[str]`**
  — build (not run) the ffmpeg argv; the last three default to the 720p30/4M
  standard. `ValueError` if `fmt` is `None`.
- **`run(config, video_size=..., framerate=...) -> None`** — orchestrate the node:
  prerequisites -> MediaMTX -> one ffmpeg per camera -> supervision -> clean
  shutdown.

## License

MIT — see [`LICENSE`](LICENSE).
