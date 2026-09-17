# Changelog

## 2.1.0 - 2026-09-17

### Restored
- JSON area preset save/load, including classic `[x, y, width, height]` presets
- processed Before/After preview
- MP4V, H.264 and XVID output choices with safe encoder fallbacks
- configurable 1–8 frame workers and ordered frame buffering
- optional hardware video-decode request with automatic software fallback
- local bilateral repair smoothing formerly exposed as blur strength
- persisted automatic-corner selections

### Fixed
- image quality presets now change real JPEG/PNG/WebP encoder parameters instead of being UI-only
- packaged GUI now receives the generated custom ICO as a runtime asset as well as an EXE icon
- processing refuses to start when no custom/corner region is selected
- H.264/XVID availability is handled without making an otherwise valid job fail unnecessarily

### Improved
- restoration and video/performance controls are separated into tabs
- area preset loader imports classic corner, inpainting, blur and margin settings
- regression tests cover restored option validation, codec fallback order, image quality and mask-local smoothing
- README documents the restored classic functions, icon, codec limitations and preset migration

## 2.0.0 - 2026-09-17

### Added
- one multilingual PL/EN Windows application replacing duplicated language builds
- automatic system-language selection with in-app switch
- modular `src/watermark_remover` architecture
- image and video restoration pipeline
- adaptive, Telea and Navier–Stokes inpainting modes
- reusable custom regions and automatic corner regions
- optional denoise, sharpening and contrast/color correction
- batch queue with progress, cancellation and per-file state
- optional audio preservation for MP4/MOV/M4V using bundled FFmpeg
- settings persisted outside the repository/application directory
- dedicated SVG/Windows application icon
- Python 3.10–3.13 CI and unit tests
- single EXE + portable ZIP + SHA256 automated GitHub Release

### Changed
- removed duplicated 46–47 KB Polish and English application files
- moved processing logic out of the GUI
- release package now ships one executable rather than two near-identical executables
- output filenames use `_restored` suffix to avoid overwriting originals

### Safety
- README and app UI explicitly scope the tool to media the user owns or has permission to modify
- originals are never overwritten automatically
