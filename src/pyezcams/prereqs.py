"""Check that the external binaries the lib needs are present, at startup."""

import shutil

# Each external tool with the concrete action to take if it is missing.
_REQUIRED = [
    (
        "ffmpeg",
        "captures and encodes. Not preinstalled on Raspberry Pi OS.\n"
        "    Install: sudo apt install ffmpeg",
    ),
    (
        "v4l2-ctl",
        "detects camera formats (part of v4l-utils).\n"
        "    Install: sudo apt install v4l-utils",
    ),
    (
        "mediamtx",
        "streaming server. Portable binary, NOT in apt.\n"
        "    Download from https://github.com/bluenviron/mediamtx/releases\n"
        "    (pick your platform: linux_arm64 Raspberry Pi, linux_amd64 PC\n"
        "    Intel/AMD, windows_amd64 Windows), unpack and put the binary on\n"
        "    the PATH (e.g. sudo mv mediamtx /usr/local/bin/)",
    ),
]


def check_prerequisites():
    """Verify ffmpeg, v4l2-ctl and mediamtx are on the PATH.

    Call at startup before touching cameras. Raises RuntimeError listing every
    missing tool and how to install it. Presence only, no version check.
    """
    missing = [(name, fix) for name, fix in _REQUIRED if shutil.which(name) is None]
    if missing:
        raise RuntimeError(_format_missing(missing))


def _format_missing(missing):
    """Build the multi-line error listing each missing tool and its fix."""
    lines = ["ERROR: missing binaries required to stream:\n"]
    for name, fix in missing:
        lines.append(f"  - {name}: {fix}")
    return "\n".join(lines)
