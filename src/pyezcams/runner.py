"""Node orchestrator: start MediaMTX + one ffmpeg per camera and keep them alive.

One Python process is the whole node. It checks prerequisites, launches the
children, and supervises them (restart on death with a small backoff) until it
receives SIGINT/SIGTERM, then kills every child cleanly.
"""

import argparse
import logging
import signal
import subprocess
import sys
import time

from .prereqs import check_prerequisites
from .match import parse_match
from .encoder import detect_encoder
from .format import detect_format
from .command import build_command, VIDEO_SIZE, FRAMERATE

# Backoff avoids tight restart loops. There is no default config: the match file
# is mandatory and passed explicitly (the lib keeps no state of its own).
RESTART_BACKOFF = 3  # seconds to wait before relaunching a dead child

log = logging.getLogger("pyezcams")

# Flipped to False by the signal handler to break the supervision loop.
_running = True


def _handle_signal(signum, frame):
    """SIGINT/SIGTERM handler: ask the supervision loop to stop."""
    global _running
    _running = False


class _Proc:
    """A supervised child: its label, its argv, and the live Popen."""

    def __init__(self, label, argv):
        self.label = label
        self.argv = argv
        self.proc = None
        self.next_try = 0.0  # monotonic time before which it won't be relaunched


def run(config, video_size=VIDEO_SIZE, framerate=FRAMERATE):
    """Run the node forever: prerequisites -> plan -> supervise -> clean shutdown.

    video_size/framerate are optional and default to the 720p30 standard.
    """
    check_prerequisites()  # fails here with a clear message if a binary is missing

    encoder = detect_encoder()
    if encoder is None:
        raise RuntimeError("no working H.264 encoder on this machine")
    log.info("encoder %s, capture %s@%s", encoder, video_size, framerate)

    procs = _plan(config, encoder, video_size, framerate)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    _supervise(procs)
    _shutdown(procs)


def _plan(config, encoder, video_size, framerate):
    """Build the children to supervise: MediaMTX + one ffmpeg per camera."""
    procs = [_Proc("mediamtx", ["mediamtx"])]
    for alias, path in parse_match(config).items():
        fmt = detect_format(path)
        if fmt is None:
            # No H264/MJPG: warn and skip this camera, keep the rest running.
            log.warning("camera '%s' (%s): no H264/MJPG, skipping", alias, path)
            continue
        mode = "copy" if fmt == "H264" else f"re-encode ({encoder})"
        log.info("camera '%s': mode %s", alias, mode)
        argv = build_command(path, alias, fmt, encoder, video_size, framerate)
        procs.append(_Proc(f"cam:{alias} [{mode}]", argv))
    return procs


def _supervise(procs):
    """Keep every child alive until a stop signal; relaunch the dead with backoff."""
    for p in procs:
        _start(p)
    while _running:
        now = time.monotonic()
        for p in procs:
            if p.proc.poll() is not None and now >= p.next_try:
                log.warning("'%s' died (rc=%s), relaunching", p.label, p.proc.returncode)
                _start(p)
        time.sleep(1)


def _start(p):
    """Launch (or relaunch) one child and arm its backoff window."""
    p.proc = subprocess.Popen(p.argv)
    p.next_try = time.monotonic() + RESTART_BACKOFF
    log.info("started '%s' (pid %s)", p.label, p.proc.pid)


def _shutdown(procs):
    """Kill every child before exiting (clean SIGINT/SIGTERM)."""
    log.info("stopping, killing children...")
    for p in procs:
        if p.proc and p.proc.poll() is None:
            p.proc.terminate()
    for p in procs:
        if p.proc:
            try:
                p.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.proc.kill()  # did not exit gracefully, force it
    log.info("all children stopped")


def main():
    """Console entry point (pyezcams)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(
        prog="pyezcams",
        description="Capture USB webcams and stream them over RTSP/WebRTC via MediaMTX.",
    )
    parser.add_argument("--config", required=True, help="path to the match txt (required)")
    parser.add_argument("--resolution", default=VIDEO_SIZE,
                        help=f"capture WxH (default {VIDEO_SIZE})")
    parser.add_argument("--fps", default=FRAMERATE,
                        help=f"capture framerate (default {FRAMERATE})")
    args = parser.parse_args()
    try:
        run(args.config, args.resolution, args.fps)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
