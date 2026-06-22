# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-06-22

### Fixed
- Works out of the box with no manual MediaMTX setup. MediaMTX's internal
  defaults (used when no `mediamtx.yml` is present) do not define an
  `all_others` path, so it rejected every publish and read with
  "path '<alias>' is not configured" (HTTP 400 to the ffmpeg publisher and to
  WebRTC/HLS readers). pyezcams now writes a minimal temporary config enabling
  the catch-all path (new `mediamtx.py` module) and launches MediaMTX pointing
  at it; the temp config is removed on shutdown. All other MediaMTX defaults
  (servers, ports) are unchanged.

## [0.1.1] - 2026-06-20

### Fixed
- Encoder detection is now hang-proof. Each encoder's 1-frame test is capped by
  the new `ENCODER_TEST_TIMEOUT` (10s) constant in `encoder.py`. A hardware
  encoder that hangs (broken driver/firmware — observed with `h264_v4l2m2m` on a
  Raspberry Pi) is discarded on timeout and detection falls through to the next
  candidate instead of blocking node startup forever. Any other subprocess error
  during the test is likewise treated as "encoder not usable" and never
  propagated. Software `libx264` remains the always-working final fallback.

## [0.1.0]

- Initial release.
