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

# A healthy encoder encodes 1 frame in well under a second. If the test runs
# longer than this, we assume the encoder is hung (e.g. a broken hardware
# driver/firmware) and treat it as unusable.
ENCODER_TEST_TIMEOUT = 10


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
    """Encode one test frame with `name`; True if ffmpeg exits 0.

    Hardened against hangs: a broken hardware encoder (bad driver/firmware)
    can wedge ffmpeg forever. We cap the test at `ENCODER_TEST_TIMEOUT`
    seconds and treat any timeout or error as "encoder not usable" so
    `detect_encoder` can move on to the next candidate instead of blocking
    node startup. On a Raspberry Pi the hardware encoder is a single shared
    device, so a hung ffmpeg would also block everyone else — never leave one
    alive.
    """
    cmd = [
        "ffmpeg", "-hide_banner",
        "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30",
        "-frames:v", "1",
        "-c:v", name,
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=ENCODER_TEST_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        # Test hung past the timeout: encoder considered not available.
        # subprocess.run already kills the child on timeout; nothing must
        # be left holding the (shared) hardware encoder.
        return False
    except Exception:
        # Any other subprocess failure: encoder not usable, never propagate.
        return False
    return result.returncode == 0
