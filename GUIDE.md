# ChromaForge — Development Guide

## Stack
- Python 3.11+ / PySide6 / NumPy / OpenCV / rawpy
- Sidecar: JSON via dataclasses
- Packaging: PyInstaller later

## Architecture (locked before coding)
- `float32` arrays in 0.0–1.0 range, `uint8` only at display/export
- Linear-light RGB working space, convert to/from source on load
- Fixed pipeline order (never reorder without migration):
  ```
  WB (Temp/Tint) → Exposure → Contrast → Highlights/Shadows/Whites/Blacks
  → Brightness → HSL → Saturation/Vibrance → Split Toning
  → RGB Curves → Sharpening → NR → Vignette → Crop/Rotate
  ```
- Versioned sidecar schema (`schemaVersion` field, neutral defaults)
- Downsampled preview (1920px long edge) for live sliders, full-res on export
- Worker thread for pipeline, signals back to UI

## Build Order (milestones)
1. **Scaffold** — PySide6 main window, file open, decode & display JPEG/PNG
2. **Core pipeline** — fixed-order pipeline module, Exposure + Contrast wired end-to-end
3. **Sidecar persistence** — JSON read/write via dataclass, verify reload
4. **Remaining tonal + color sliders**
5. **HSL panel** (8 bands, smooth weighted blends)
6. **Split Toning**
7. **RGB Curves** (custom QPainter widget, LUT-based apply)
8. **Detail (sharpen/NR) + Vignette**
9. **Histogram + Before/After**
10. **Crop/Rotate/Flip/Zoom/Pan**
11. **Undo/Redo** (QUndoStack)
12. **RAW import** (rawpy)
13. **Export** (full-res, format/quality options)
14. **Polish** — keyboard shortcuts, slider reset, error states

## UI Conventions
- Dark theme via `.qss` stylesheet
- Collapsible panels: Tonal / Color / HSL / Split Toning / Curves / Detail / Vignette / Crop
- Histogram always visible
- Each slider: draggable track + QDoubleSpinBox + double-click reset
- Before/After: `\` key + button

## Rules
- No per-pixel Python loops — NumPy/OpenCV only
- Type hints everywhere
- Pure functions for each operation (input + params → output)
- One file per panel widget
- NEVER modify source image file

## Out of Scope (Phase 1)
Local adjustments, 3-way color wheels, 3D LUTs, waveforms, batch editing, catalog, presets.
