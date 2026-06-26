# Project Brief: ChromaForge — Non-Destructive Photo Color Grading App (Phase 1: Global Tools)

## Your Role

You are building **Phase 1** of a professional-grade, non-destructive photo color grading desktop application for **Windows and Linux**. This is a real product, not a prototype — write production-quality, well-structured code from the start. Phase 1 is **global adjustments only** — no masking, no local tools, no LUTs. Do not add any of those even if they seem easy; they are explicitly deferred (see "Out of Scope" below) and adding them now will complicate the architecture for later phases.

Read this entire document before writing any code. If anything is ambiguous, make a reasonable decision, state the assumption in a comment or commit message, and move on — don't stall waiting for clarification on small things.

---

## Product Philosophy

- **Non-destructive**: the original image file is NEVER modified. Every edit is stored as a set of numeric/parametric values in a sidecar file, applied on top of the original at render time.
- **Fast**: real-time slider feedback on full-resolution images, including RAW. No spinner-and-wait UX for basic tonal/color adjustments.
- **No bloat, no subscription**: a focused tool that does global grading extremely well, not a kitchen-sink app.
- **Cross-platform**: must build and run natively on both Windows and Linux from the same codebase.

---

## Tech Stack (fixed for this project)

- **Language**: Python 3.11+.
- **UI framework**: Qt via **PySide6**. Use Qt Widgets (QSlider, QGraphicsView, custom QPainter-based curve editor) rather than QML unless you have a strong reason — Widgets are more predictable for dense control panels like this.
- **Image processing**: **NumPy** for array math, **OpenCV** (`opencv-python` / `opencv-contrib-python`) for image decode/encode, color space conversions, filtering (sharpening, noise reduction, vignette), and any built-in ops that map directly to OpenCV functions (use OpenCV's optimized C implementations instead of hand-rolled NumPy loops wherever a suitable function exists).
- **RAW decoding**: use `rawpy` (Python bindings to LibRaw) — do not write a custom demosaicing algorithm.
- **Curves rendering**: implement Bezier/spline curve evaluation in NumPy (vectorized lookup-table generation: compute a 256 or 65536-entry LUT from the curve control points, then apply via `cv2.LUT` or NumPy fancy-indexing — never apply curves pixel-by-pixel in a Python loop).
- **Edit storage**: a JSON sidecar file per image for edit parameters (schema below) — plain Python dicts via the `json` module is sufficient, no need for an ORM. If you want a lightweight project/recents list, SQLite via Python's built-in `sqlite3` module is fine for that app-state layer only (separate concern from the sidecar).
- **GPU acceleration (optional, only if CPU path can't hit real-time)**: OpenCV's CUDA module (`cv2.cuda`) if available on the target machine, with a CPU fallback — do not make GPU a hard requirement, since this needs to run on arbitrary Windows/Linux machines without guaranteed CUDA support.
- **Packaging**: PyInstaller (or similar) for distributing as a native-feeling executable on both platforms — not required for early development, but keep imports/structure compatible with it (avoid dynamic import tricks that break freezing).

---

## Critical Architecture Decisions (lock these in before writing feature code)

These are invisible to the user but extremely painful to change later. Decide and document them in `ARCHITECTURE.md` first:

1. **Internal pixel representation**: load and process images as NumPy `float32` arrays in the 0.0–1.0 range, regardless of the source file's bit depth (8-bit JPEG, 14-bit RAW, etc.). Only convert to `uint8` at the very end, for display in the QImage/QPixmap preview or for final export. Never do tonal/color math directly on `uint8` arrays — it causes visible banding, especially in skies and skin tones.
2. **Working color space**: define one working color space (e.g. linear-light RGB) that all adjustments are computed in, with explicit conversion to/from the source's color space on load (OpenCV decodes as BGR — convert to RGB immediately and document this so it isn't a recurring source of bugs) and to the display/output profile on export. Document this explicitly in `ARCHITECTURE.md`.
3. **Fixed pipeline order**: adjustments MUST be applied in a single, fixed, documented order every time, e.g.:
   ```
   White Balance (Temp/Tint) → Exposure → Contrast → Highlights/Shadows/Whites/Blacks
   → Brightness → HSL (per-channel) → Saturation/Vibrance → Split Toning
   → RGB Curves → Sharpening → Noise Reduction → Vignette → Crop/Rotate (geometry last)
   ```
   Write this order down in `ARCHITECTURE.md` and never reorder it without a migration plan for existing sidecar files. Implement this as a single ordered pipeline function (e.g. a list of `(name, function, params)` steps) so the order is enforced in one place, not scattered across the codebase.
4. **Edit sidecar schema**: version it from day one. Example:
   ```json
   {
     "schemaVersion": 1,
     "sourceFile": "IMG_0421.CR3",
     "edits": {
       "whiteBalance": { "temperature": 0, "tint": 0 },
       "tonal": { "exposure": 0, "contrast": 0, "highlights": 0, "shadows": 0, "whites": 0, "blacks": 0, "brightness": 0 },
       "color": { "saturation": 0, "vibrance": 0, "hue": 0 },
       "hsl": { "red": {...}, "orange": {...}, "yellow": {...}, "green": {...}, "aqua": {...}, "blue": {...}, "purple": {...}, "magenta": {...} },
       "splitToning": { "shadowHue": 0, "shadowSat": 0, "highlightHue": 0, "highlightSat": 0, "balance": 0 },
       "curves": { "master": [...points...], "red": [...], "green": [...], "blue": [...] },
       "detail": { "sharpenAmount": 0, "sharpenRadius": 0, "noiseLuminance": 0, "noiseColor": 0 },
       "vignette": { "amount": 0, "midpoint": 50, "roundness": 0, "feather": 50 },
       "geometry": { "crop": null, "rotationDegrees": 0, "flipH": false, "flipV": false }
     },
     "history": []
   }
   ```
   Every value defaults to a neutral/zero state so a freshly-imported image renders identically to the source. Represent this in Python as a `dataclass` (or nested dataclasses) with a `to_dict()`/`from_dict()` pair, not a loose dict passed around everywhere.

---

## Phase 1 Feature List (build all of these)

### 1. Global Tonal & Brightness
- Exposure, Contrast, Highlights, Shadows, Whites, Blacks, Brightness — standard photographic-stop / luminance-curve behavior as in Lightroom/Capture One. Each is a single slider, range roughly -100 to +100 (Exposure in stops, e.g. -5 to +5).

### 2. Global Color
- Saturation, Vibrance (vibrance must protect skin-tone hues from clipping into orange/red), Temperature, Tint, Hue (rotates the full color wheel).

### 3. HSL Per-Channel Panel
- Eight color bands: Red, Orange, Yellow, Green, Aqua, Blue, Purple, Magenta.
- Each band has independent Hue, Saturation, and Luminance sliders.
- This is still global (affects that hue range across the whole frame, no masking). Implement via HSV/HLS conversion (`cv2.cvtColor`) and per-band masks derived from the hue channel, applied as smooth weighted blends (not hard cutoffs) to avoid banding between bands.

### 4. Split Toning
- Independent Hue + Saturation for Shadows and for Highlights, plus a Balance slider to control the tonal split point. This is the lightweight, global stand-in for full 3-way color wheels — do not build Lift/Gamma/Gain wheels in Phase 1.

### 5. RGB Curves
- Four independent editable curves: Master, Red, Green, Blue.
- Each curve is a draggable spline/Bezier through control points on a 0–255 (or 0–1) input/output graph, rendered with a custom `QGraphicsView`/`QPainter` widget.
- Must support adding, dragging, and deleting points. Apply via precomputed LUTs (see Tech Stack section) for performance.

### 6. Detail
- **Sharpening**: amount + radius (unsharp-mask via `cv2.GaussianBlur` + weighted subtraction).
- **Noise Reduction**: separate luminance and color noise sliders (e.g. `cv2.fastNlMeansDenoisingColored` or a bilateral filter, tuned for responsiveness).

### 7. Vignette
- Parametric only (amount, midpoint, roundness, feather) — radial darkening/lightening from center, generated as a precomputed radial gradient mask multiplied into the image. No mask painting.

### 8. Analytical & Comparison Tools
- **Histogram**: live RGB histogram (`cv2.calcHist` or NumPy `bincount`), rendered in a small Qt widget, updates in real time as sliders move.
- **Before/After**: a toggle (and ideally a split-screen drag handle) between original and edited.

### 9. Composition & Navigation
- Crop & Straighten (drag a box, rotate to fix horizon).
- Rotate 90° CW/CCW, flip horizontal/vertical.
- Zoom & Pan (smooth, supports pixel-level inspection) — implement via `QGraphicsView`'s built-in scaling/panning rather than custom hit-testing.

### 10. Workflow & Safety
- Full Undo/Redo history stack (Ctrl+Z / Ctrl+Y), effectively unlimited depth. Qt's `QUndoStack`/`QUndoCommand` is a good fit here — use it rather than rolling a custom stack.
- Import: JPEG, PNG, TIFF, and at least one common RAW format (e.g. CR2/CR3/NEF/ARW, via `rawpy`), never modifying the source file.
- Export: JPEG, PNG, TIFF, with a quality/compression setting and an output color space choice (sRGB at minimum).

### 11. Lens Corrections (basic, if time allows in Phase 1 — otherwise first thing in Phase 1.5)
- Auto-apply vignetting/distortion correction from embedded EXIF lens data when available (read via `exifread` or `rawpy`'s metadata). Treat as stretch goal, not blocking.

---

## Out of Scope for Phase 1 (do not build, do not stub UI for these yet)

- Local adjustments: gradient filters, radial filters, brush masking, AI/subject-select masking.
- 3-way color wheels (Lift/Gamma/Gain).
- 3D LUT import/export (.cube).
- Waveform monitor / vectorscope (histogram only for now).
- Batch editing or syncing edits across multiple images.
- Catalog/library management (folders, star ratings, flags, collections) — Phase 1 is single-image-at-a-time editing with simple file open/save.
- Presets system.

If you find yourself building any of these "because it's easy while I'm in this code," stop — log it as a future-phase note instead.

---

## UI/UX Guidelines

- Dark theme by default (standard for color-grading tools — reduces eye strain and avoids skewing perceived contrast/color of the image being graded). Use a Qt stylesheet (`.qss`) for this rather than per-widget styling.
- Right-side (or left-side, pick one and be consistent) collapsible panel structure (`QDockWidget` or custom collapsible `QGroupBox`es) grouping: Tonal / Color / HSL / Split Toning / Curves / Detail / Vignette / Crop — similar information architecture to Lightroom's Develop module, but don't copy its visual style.
- Histogram should be persistently visible, not hidden in a tab.
- Sliders need: draggable track, numeric input fallback (click number, type exact value — pair each `QSlider` with a `QSpinBox`/`QDoubleSpinBox`), double-click-to-reset-to-default.
- Before/After should be a single keyboard shortcut (e.g. `\`) as well as a button.

---

## Performance Requirements

- Slider drag must visibly update the preview at interactive framerates (target: no perceptible lag at 1080p preview resolution; full-res render can happen on slider release/debounce if needed for very large RAW files).
- Use a downsampled preview buffer (e.g. long edge capped at ~1920px) for live interaction, full-resolution render only for export and final confirmation — document this strategy in `ARCHITECTURE.md`.
- Debounce slider drag events (e.g. via `QTimer`) so the full pipeline isn't re-run on every single pixel of mouse movement — recompute on a short delay or on release, with a cheap/partial update during the drag itself if needed.
- Run the processing pipeline on a worker thread (`QThread` or `concurrent.futures`) rather than the Qt main/UI thread, so the UI never freezes during a recompute — communicate results back via Qt signals.
- Vectorize everything: any per-pixel Python `for` loop is a bug. If you find yourself writing one, replace it with NumPy array operations or an OpenCV function.

---

## Suggested Build Order (milestones)

1. **Scaffold**: PySide6 project structure, main window, file-open dialog, decode and display a JPEG/PNG via OpenCV → QImage.
2. **Core pipeline**: implement the fixed-order processing pipeline as a Python module with just Exposure + Contrast wired up, confirm real-time preview works end-to-end (slider → worker thread → processed NumPy array → QImage → displayed).
3. **Sidecar persistence**: wire up the JSON sidecar read/write (via the dataclass schema), confirm edits persist and reload correctly.
4. **Remaining tonal + color sliders** (Highlights/Shadows/Whites/Blacks/Brightness, Saturation/Vibrance/Temp/Tint/Hue).
5. **HSL panel**.
6. **Split Toning**.
7. **RGB Curves** (this is the most UI-complex piece — budget extra time for the custom curve widget).
8. **Detail (sharpen/NR) + Vignette**.
9. **Histogram + Before/After**.
10. **Crop/Rotate/Flip/Zoom/Pan**.
11. **Undo/Redo across all of the above** (via `QUndoStack`).
12. **RAW import support** (`rawpy`).
13. **Export pipeline** (full-res render + format/quality options).
14. **Polish pass**: keyboard shortcuts, slider reset behavior, error states (corrupt file, unsupported RAW variant, etc.).

Work through these roughly in order — don't build Curves before the core pipeline and persistence are solid, since every later feature has to slot into that same pipeline correctly.

---

## Coding Standards

- Use type hints throughout (`def apply_exposure(img: np.ndarray, stops: float) -> np.ndarray:`), and run `mypy` if convenient.
- Be explicit and avoid "magic" defaults — every adjustment parameter should have a named constant for its neutral/default value and its min/max range, not hardcoded inline.
- Comment the processing pipeline order clearly at the point where it's executed, referencing back to `ARCHITECTURE.md`.
- Write small, testable, pure functions for each tonal/color operation (input NumPy array + params → output NumPy array, no side effects) so they can be unit tested with `pytest` independently of the Qt UI layer.
- Keep UI code organized as one Qt widget/class per control group (one file per panel) rather than one giant window file with everything inline.
- Never write a per-pixel Python loop over image data — see Performance Requirements.

---

## Definition of Done for Phase 1

A user can: import a JPEG/PNG/TIFF/RAW file → apply any combination of the listed global adjustments with real-time preview → see an accurate live histogram → toggle before/after → crop/rotate/flip → undo/redo through their full edit history → close and reopen the app with edits intact (sidecar reload) → export a final JPEG/PNG/TIFF that reflects all edits, with the original source file completely untouched on disk.
