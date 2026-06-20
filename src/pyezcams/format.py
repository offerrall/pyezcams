"""Detect a camera's capture format via v4l2-ctl.

Portability: v4l2-ctl is Linux-only, which suits the Linux nodes the
`/dev/v4l/by-path/...` match paths point to. Windows capture would need a
DirectShow variant (`ffmpeg -list_devices`); out of scope here.
"""

import subprocess

# Preference: native H264 (copy, no re-encode) > MJPG (re-encode).
# YUYV is intentionally ignored (capped to very few fps).
PREFERRED_FORMATS = ["H264", "MJPG"]


def detect_format(usb_path):
    """Return the best capture format the camera offers, or None.

    "H264" (native, copied with `-c:v copy`, ~0 CPU) is preferred over "MJPG"
    (must be re-encoded). None if it offers neither.
    """
    available = _list_formats(usb_path)
    for fmt in PREFERRED_FORMATS:
        if fmt in available:
            return fmt
    return None


def _list_formats(usb_path):
    """Return the preferred formats reported by `v4l2-ctl --list-formats-ext`."""
    result = subprocess.run(
        ["v4l2-ctl", "--device", usb_path, "--list-formats-ext"],
        capture_output=True,
        text=True,
    )
    available = set()
    for fmt in PREFERRED_FORMATS:
        # v4l2-ctl prints each format code quoted, e.g.  [1]: 'H264' (...).
        if f"'{fmt}'" in result.stdout:
            available.add(fmt)
    return available
