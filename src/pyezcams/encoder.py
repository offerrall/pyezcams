"""Detect the best available, working H.264 encoder."""

import subprocess

# Preference order: hardware first, software (libx264) as a last resort.
PREFERRED_ENCODERS = [
    "h264_nvenc",
    "h264_qsv",
    "h264_vaapi",
    "h264_v4l2m2m",
    "libx264",
]


def detect_encoder():
    """Return the first preferred encoder that is present and actually works.

    For each candidate listed by `ffmpeg -encoders`, runs a real 1-frame test
    and returns the first to exit 0. Returns None if none works.
    """
    available = _list_encoders()
    for name in PREFERRED_ENCODERS:
        if name in available and _test_encoder(name):
            return name
    return None


def _list_encoders():
    """Return the set of preferred encoders reported by `ffmpeg -encoders`."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
    )
    available = set()
    for candidate in PREFERRED_ENCODERS:
        # In ffmpeg's table the name appears as a whitespace-delimited word.
        if f" {candidate} " in result.stdout:
            available.add(candidate)
    return available


def _test_encoder(name):
    """Encode one test frame with `name`; True if ffmpeg exits 0."""
    cmd = [
        "ffmpeg", "-hide_banner",
        "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30",
        "-frames:v", "1",
        "-c:v", name,
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0
