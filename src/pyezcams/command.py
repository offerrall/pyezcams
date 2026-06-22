"""Build (not run) the ffmpeg command for a single camera.

Defaults (720p30 surveillance standard, overridable per call):
  VIDEO_SIZE 1280x720 · FRAMERATE 30 · BITRATE 4M · RTSP_BASE localhost:8554

Per case:
  - H264 (copy):  capture at video_size/framerate, copy the native stream
    (`-c:v copy`, ~0 CPU). bitrate does NOT apply (nothing is re-encoded).
  - MJPG (re-encode): capture at video_size/framerate, re-encode with the
    detected encoder at `bitrate` (GOP fixed at 60 = 2s @30fps).
"""

# Module-level defaults; tweak here to change the standard for every camera.
VIDEO_SIZE = "1280x720"   # 720p
FRAMERATE = "30"          # 30 fps
BITRATE = "4M"            # re-encode (MJPG) case only
RTSP_BASE = "rtsp://localhost:8554"  # MediaMTX RTSP endpoint


def build_command(usb_path, alias, fmt, encoder,
                  video_size=VIDEO_SIZE, framerate=FRAMERATE, bitrate=BITRATE):
    """Build the ffmpeg argv for one camera (does not run it).

    video_size/framerate/bitrate are optional and default to the 720p30/4M
    standard. `fmt="H264"` copies (bitrate ignored); `fmt="MJPG"` re-encodes
    with `encoder`. Raises ValueError if `fmt` is None (unusable camera).
    """
    if fmt == "H264":
        return _build_copy(usb_path, alias, video_size, framerate)
    if fmt == "MJPG":
        return _build_reencode(usb_path, alias, encoder, video_size, framerate, bitrate)
    raise ValueError(f"unusable camera {usb_path!r}: no H264/MJPG format")


def _build_copy(usb_path, alias, video_size, framerate):
    """Native H264: copy as-is, no encoder involved (bitrate not applicable)."""
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "warning",
        "-f", "v4l2", "-input_format", "h264",
        "-video_size", video_size, "-framerate", framerate, "-i", usb_path,
        "-c:v", "copy",
        "-rtsp_transport", "tcp", "-f", "rtsp", f"{RTSP_BASE}/{alias}",
    ]


def _build_reencode(usb_path, alias, encoder, video_size, framerate, bitrate):
    """MJPG: re-encode with the detected hardware/software encoder.

    h264_qsv: decode MJPG and encode H264 fully on Intel GPU via QSV
              (~0 CPU). Requires -init_hw_device and -c:v mjpeg_qsv on input.
    h264_vaapi: decode on CPU, upload frames to GPU via VAAPI for encode.
    others (libx264, etc.): full software path.
    """
    if encoder == "h264_qsv":
        # Full hardware path: MJPG decode + H264 encode both on Intel QSV GPU.
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "warning",
            "-init_hw_device", "qsv=qsv:hw",
            "-c:v", "mjpeg_qsv",
            "-fflags", "nobuffer", "-flags", "low_delay",
            "-probesize", "32", "-analyzeduration", "0",
            "-f", "v4l2", "-input_format", "mjpeg",
            "-video_size", video_size, "-framerate", framerate, "-i", usb_path,
            "-c:v", "h264_qsv", "-b:v", bitrate, "-g", "60",
            "-rtsp_transport", "tcp", "-f", "rtsp", f"{RTSP_BASE}/{alias}",
        ]
    if encoder == "h264_vaapi":
        # VAAPI needs the render device declared up front and the frames
        # uploaded to the GPU (format=nv12,hwupload). It also rejects the
        # software-style -b:v/-g/-bf flags, so those are omitted here.
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "warning",
            "-fflags", "nobuffer", "-flags", "low_delay",
            "-probesize", "32", "-analyzeduration", "0",
            "-vaapi_device", "/dev/dri/renderD128",
            "-f", "v4l2", "-input_format", "mjpeg",
            "-video_size", video_size, "-framerate", framerate, "-i", usb_path,
            "-vf", "format=nv12,hwupload",
            "-c:v", encoder,
            "-rtsp_transport", "tcp", "-f", "rtsp", f"{RTSP_BASE}/{alias}",
        ]
    # Software fallback (libx264, h264_v4l2m2m, etc.)
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "warning",
        "-fflags", "nobuffer", "-flags", "low_delay",
        "-probesize", "32", "-analyzeduration", "0",
        "-f", "v4l2", "-input_format", "mjpeg",
        "-video_size", video_size, "-framerate", framerate, "-i", usb_path,
        "-c:v", encoder, "-b:v", bitrate, "-g", "60",
        "-bf", "0",
        "-rtsp_transport", "tcp", "-f", "rtsp", f"{RTSP_BASE}/{alias}",
    ]