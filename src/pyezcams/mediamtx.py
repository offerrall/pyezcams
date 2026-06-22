"""Generate MediaMTX's config and its launch command.

Why this exists: MediaMTX's *internal* defaults (used when it finds no
mediamtx.yml) do NOT define an `all_others` path, so out of the box it rejects
every publish and read with "path '<alias>' is not configured" -- HTTP 400 to
the ffmpeg publisher, the same error to WebRTC/HLS readers. To make pyezcams
work with no manual setup, we write a tiny config that enables the catch-all
path and launch MediaMTX pointing at it. Everything else keeps MediaMTX's
defaults (servers, ports), so only the path behaviour changes.
"""

import os
import tempfile

_CONFIG = "paths:\n  all_others:\n"


def write_config():
    fd, path = tempfile.mkstemp(prefix="pyezcams-mediamtx-", suffix=".yml")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(_CONFIG)
    return path


def remove_config(path):
    try:
        os.remove(path)
    except OSError:
        pass


def build_command(config_path):
    return ["mediamtx", config_path]
