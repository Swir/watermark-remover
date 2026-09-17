<div align="center">

<img src="assets/watermark-remover.svg" width="112" alt="Watermark Remover Pro icon">

# Watermark Remover Pro v2.1

### Image & video restoration with selectable region inpainting

**Python · OpenCV · ttkbootstrap · PL/EN · Windows EXE**

[![CI](https://github.com/Swir/watermark-remover/actions/workflows/ci.yml/badge.svg)](https://github.com/Swir/watermark-remover/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Swir/watermark-remover)](https://github.com/Swir/watermark-remover/releases)
[![Author](https://img.shields.io/badge/by-Swir-4cc9ff)](https://github.com/Swir)

</div>

Watermark Remover Pro is a desktop restoration tool for cleaning selected overlays, timestamps, labels, logos or damaged regions from **media you own or are authorized to edit**. It uses OpenCV inpainting to reconstruct pixels from surrounding image information. Results depend on scene complexity and mask selection; this is a restoration tool, not a generative replacement system.

## v2.1 regression recovery

The v2 modernization successfully replaced two duplicated Polish/English applications with one maintainable codebase, but the audit found several working controls from the classic app that had disappeared. v2.1 restores those capabilities without bringing back the old duplicated scripts.

### Restored from the classic app

- **Save areas / Load areas** JSON presets, including compatibility with the old preset schema
- processed **Before / After preview** before starting a long job
- **MP4V, H.264 and XVID** video codec choices with safe encoder fallback
- configurable **1–8 frame workers**
- optional processed-frame **buffering** while preserving output frame order
- optional **hardware-accelerated video decode request** with automatic software fallback
- adjustable **repair smoothing** (bilateral smoothing only inside the repaired mask)
- persisted automatic-corner choices
- application icon loaded inside the packaged GUI, not only attached to the EXE

The audit intentionally did **not** restore old controls that never had a working backend. The current UI only exposes options that are connected to processing code.

## Architecture

```text
main.py
src/watermark_remover/
  app.py         desktop UI, presets, preview, queue, progress/cancel
  engine.py      masks, inpainting, local smoothing, post-processing
  video.py       image/video I/O, ordered worker pipeline, codecs, audio remux
  models.py      areas and validated processing options
  settings.py    persistent user settings
  i18n.py        Polish/English translations
assets/
  watermark-remover.svg  project/README icon
  watermark-remover.ico  generated for Windows builds and bundled into the EXE
tools/
  build_icon.py          custom Windows icon generator
```

## Features

- images: JPG, PNG, BMP, WebP, TIFF
- videos: MP4, MOV, AVI, MKV, M4V, WebM input
- manual multi-region selection on a preview frame
- processed Before/After preview
- reusable area presets saved as JSON
- automatic top-left/top-right/bottom-left/bottom-right masks
- adaptive texture-based method plus explicit Telea and Navier–Stokes modes
- configurable inpaint radius, mask margin, edge feathering and local repair smoothing
- optional denoise, sharpen and automatic contrast/color correction
- batch queue with per-file state
- progress indicator and cancellation
- 1–8 ordered frame-processing workers with optional buffering
- optional hardware video-decoding request with safe fallback
- MP4V / H.264 / XVID output selection; H.264 falls back when the local OpenCV build lacks an encoder
- image output quality presets that now change real JPEG/PNG/WebP encoder parameters
- optional MP4 video audio preservation through FFmpeg
- originals are never overwritten; outputs get `_restored`
- PL/EN UI selected from the system locale with a manual switch
- settings saved in the user's home profile, not next to the EXE
- dedicated project icon shown above and used by Windows builds

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
3. Enable corner regions and/or use **Select areas** to draw custom rectangles on the first item.
4. Optionally save those regions as a JSON preset for another session.
5. Use **Preview result** to compare the original first frame with the processed result.
6. Pick Adaptive/Telea/Navier–Stokes, smoothing and optional post-processing.
7. For video, choose codec, worker count, buffering, hardware decode request and optional audio preservation.
8. Start processing. Progress and per-file state are shown in the main window.

Custom pixel rectangles are reused for batch items. If batch files have different dimensions/compositions, process them in separate groups or rely on proportional corner masks.

## Area preset compatibility

v2.1 reads both the current dictionary-based area format and classic presets where an area was stored as `[x, y, width, height]`. Classic `corners`, `inpaint_method`, `blur_strength` and `margin_size` values are imported when present.

## Video codec notes

- **MP4V** is the most compatible default and writes `.mp4`.
- **H.264** writes `.mp4` when the installed OpenCV/FFmpeg backend provides an H.264 encoder; otherwise the writer falls back to MP4V and records that in the log.
- **XVID** writes `.avi`; OpenCV may fall back to MJPG if XVID is unavailable.
- Audio preservation is applied to MP4/MOV/M4V-style outputs when FFmpeg remuxing succeeds. AVI/XVID processing is video-only, matching the practical limitation of the classic OpenCV writer path.

## Quality notes

OpenCV inpainting is strongest on small overlays over relatively continuous textures. Large masks over faces, complex text, motion or detailed geometry can produce visible artifacts. Start with the smallest practical mask and moderate radius.

The **Image output quality** setting now changes actual encoder parameters for JPEG, PNG and WebP instead of being a cosmetic setting. Video quality is governed primarily by the selected codec/backend.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

CI validates the core on Python 3.10, 3.11, 3.12 and 3.13, including restored option validation, mask-local smoothing, image quality parameters, codec fallback order and the image pipeline.

## Release

The Windows workflow runs tests, generates the custom icon, bundles that icon into the GUI, builds `WatermarkRemoverPro.exe`, performs an artifact smoke check, creates a portable ZIP and publishes SHA256 checksums. A merge commit containing `[release]` publishes the current version only after CI is green.

## Responsible use

Use this software only on images/videos you created, own, or have permission to modify. Do not use it to misrepresent ownership or redistribute protected material without authorization.

## Author

Developed by **Swir** — https://github.com/Swir
