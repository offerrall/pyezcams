# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
