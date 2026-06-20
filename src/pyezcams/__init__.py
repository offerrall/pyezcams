"""pyezcams — minimal, stateless toolkit to stream USB webcams via MediaMTX.

Public API:
  - parse_match: read a `usb_path = alias` match file.
  - check_prerequisites: verify ffmpeg, v4l2-ctl and mediamtx are on the PATH.
  - detect_encoder: pick the best working H.264 encoder.
  - detect_format: pick a camera's best capture format (H264 > MJPG).
  - build_command: build (not run) the ffmpeg argv for one camera.
  - run: orchestrate the node (MediaMTX + one ffmpeg per camera).
"""

__version__ = "0.1.0"

from .match import parse_match
from .encoder import detect_encoder
from .format import detect_format
from .command import build_command
from .prereqs import check_prerequisites
from .runner import run

__all__ = [
    "__version__",
    "parse_match",
    "detect_encoder",
    "detect_format",
    "build_command",
    "check_prerequisites",
    "run",
]
