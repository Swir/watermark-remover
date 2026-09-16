<div align="center">

<img src="assets/watermark-remover.svg" width="112" alt="Watermark Remover Pro icon">

# Watermark Remover Pro v2

### Image & video restoration with selectable region inpainting

**Python · OpenCV · ttkbootstrap · PL/EN · Windows EXE**

[![CI](https://github.com/Swir/watermark-remover/actions/workflows/ci.yml/badge.svg)](https://github.com/Swir/watermark-remover/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Swir/watermark-remover)](https://github.com/Swir/watermark-remover/releases)
[![Author](https://img.shields.io/badge/by-Swir-4cc9ff)](https://github.com/Swir)

</div>

Watermark Remover Pro is a desktop restoration tool for cleaning selected overlays, timestamps, labels, logos or damaged regions from **media you own or are authorized to edit**. It uses OpenCV inpainting to reconstruct pixels from the surrounding image. Results depend on scene complexity and the selected mask; it is a restoration tool, not a generative replacement system.

## v2 modernization

The previous repository maintained two almost identical ~46–47 KB applications, one Polish and one English. v2 replaces them with **one multilingual codebase and one Windows executable**.

```text
main.py
src/watermark_remover/
  app.py         desktop UI, batch queue, progress/cancel
  engine.py      masks, inpainting, post-processing
  video.py       image/video I/O and optional audio remux
  models.py      areas and processing options
  settings.py    persistent user settings
  i18n.py        Polish/English translations
assets/
  watermark-remover.svg
tools/
  build_icon.py  Windows .ico generator
```

## Features

- images: JPG, PNG, BMP, WebP, TIFF
- videos: MP4, MOV, AVI, MKV, M4V, WebM input
- manual multi-region selection on a preview frame
- automatic top-left/top-right/bottom-left/bottom-right masks
- adaptive texture-based method plus explicit Telea and Navier–Stokes modes
- configurable inpaint radius, mask margin and edge feathering
- optional denoise, sharpen and automatic contrast/color correction
- batch queue with per-file state
- progress indicator and cancellation
- optional video audio preservation through FFmpeg
- originals are never overwritten; outputs get `_restored`
- PL/EN UI selected from the system locale with a manual switch
- settings saved in the user's home profile, not next to the EXE
- dedicated project icon and professional Windows Release pipeline

## Requirements

- Python 3.10–3.13
- OpenCV 4.10+
- NumPy 2.x
- Pillow 10+
- ttkbootstrap 1.x
- imageio-ffmpeg 0.5+

## Run from source

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -e .
python main.py
```

On Linux/macOS use the platform's virtual-environment activation command.

## Workflow

1. Add one or more media files.
2. Pick an output directory.
3. Use **Preview / select areas** to draw one or more custom rectangles on the first file, and/or enable corner regions.
4. Pick Adaptive/Telea/Navier–Stokes and optional post-processing.
5. Start processing. For video, the app reports frame progress and can preserve audio when FFmpeg remuxing is available.

Custom pixel rectangles are reused for batch items. If batch files have different dimensions/compositions, process them in separate groups or rely on proportional corner masks.

## Quality notes

OpenCV inpainting is strongest on small overlays over relatively continuous textures. Large masks over faces, complex text, motion or detailed geometry can produce visible artifacts. Start with the smallest practical mask and moderate radius.

Video processing writes frames through OpenCV. MP4/MOV/M4V outputs optionally remux the original audio using `imageio-ffmpeg`; when remuxing is unavailable or fails, v2 safely falls back to the processed video stream rather than losing the whole job.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

CI validates the core on Python 3.10, 3.11, 3.12 and 3.13.

## Release

The Windows workflow builds a single `WatermarkRemoverPro.exe`, a portable ZIP and SHA256 checksums. A merge commit containing `[release]` publishes v2 automatically after tests pass.

## Responsible use

Use this software only on images/videos you created, own, or have permission to modify. Do not use it to misrepresent ownership or redistribute protected material without authorization.

## Author

Developed by **Swir** — https://github.com/Swir
