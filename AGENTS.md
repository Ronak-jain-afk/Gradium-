# ChromaForge — Agent Guide

## Project

Non-destructive photo color grading desktop app (Windows + Linux). Phase 1 = global adjustments only (no masking, LUTs, presets, catalog).

Fixed tech stack: Python 3.11+ / PySide6 / NumPy / OpenCV / rawpy.

## Key reference files

| File | What |
|------|------|
| `plan.md` | Full spec: architecture, pipeline order, build order, feature list, performance requirements |
| `PRODUCT.md` | Register, users, brand personality, design principles |
| `DESIGN.md` | Visual system: warm charcoal palette, amber accent, Inter, restrained motion |

## Architecture locked before coding

- `float32` arrays in 0.0–1.0 range; only convert to `uint8` at display/export. No tonal math on `uint8`.
- Working color space: linear-light RGB. Convert from BGR→RGB on load (OpenCV decodes as BGR).
- Fixed pipeline order (never reorder without migration):
  WB → Exposure → Contrast → Hi/Sh/Wh/Bl → Brightness → HSL → Sat/Vibrance → Split Toning → RGB Curves → Sharpening → NR → Vignette → Crop/Rotate
- Implement as list of `(name, fn, params)` steps in one place.
- Versioned JSON sidecar per image via dataclass with `to_dict()`/`from_dict()`.
- Downsampled preview (1920px long edge) for live sliders; full-res on export.
- Processing on worker thread (`QThread`/`concurrent.futures`), signal results back.
- Debounce slider drags via `QTimer`.

## UI conventions

- Dark theme via `.qss` stylesheet.
- Collapsible panels: Tonal / Color / HSL / Split Toning / Curves / Detail / Vignette / Crop.
- Histogram always visible.
- Every slider: draggable track + `QDoubleSpinBox` + double-click reset.
- Before/After: `\` key + button.
- Refer to `DESIGN.md` for the visual system (warm charcoal + amber accent, Inter typeface).

## Coding standards

- Type hints throughout.
- Pure functions for each operation: `fn(img: np.ndarray, **params) -> np.ndarray`.
- One file per panel widget.
- Named constants for neutral/default values and min/max ranges (no inline magic).
- No per-pixel Python loops over image data — NumPy array ops or OpenCV only.
- Keep imports PyInstaller-compatible (no dynamic import tricks).

## Build order (milestones)

1. Scaffold: main window, file-open, decode & display JPEG/PNG via OpenCV→QImage
2. Core pipeline: fixed-order module with Exposure + Contrast, real-time preview
3. Sidecar persistence: JSON read/write, verify reload
4. Remaining tonal + color sliders
5. HSL panel (8 bands, smooth weighted blends via HSV conversion)
6. Split toning
7. RGB Curves (custom QPainter widget, LUT-based apply)
8. Detail (sharpen/NR) + Vignette
9. Histogram + Before/After
10. Crop/Rotate/Flip/Zoom/Pan
11. Undo/Redo (QUndoStack)
12. RAW import (rawpy)
13. Export pipeline (full-res, format/quality options)
14. Polish: shortcuts, slider reset, error states

## Out of scope (Phase 1)

Local adjustments, 3-way color wheels, 3D LUTs, waveform/vectorscope, batch editing, catalog/library, presets.

## Design context

See `PRODUCT.md` (strategic) and `DESIGN.md` (visual tokens + rules). `DESIGN.md` is a seed — re-run `$impeccable document` once UI code exists to extract real tokens.
