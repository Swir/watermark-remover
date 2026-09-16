# Changelog

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
