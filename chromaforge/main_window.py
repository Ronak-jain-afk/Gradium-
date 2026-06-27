from pathlib import Path

import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QLabel, QMessageBox, QSplitter, QStatusBar, QToolBar,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QUndoStack, QUndoCommand
from PySide6.QtWidgets import QApplication

from .core import (
    load_image, compute_downsampled, PipelineThread,
    Sidecar, load_sidecar, save_sidecar, constants,
)
from .widgets import ImageViewer, HistogramWidget
from .widgets.export_dialog import ExportDialog
from .widgets.panels import (
    TonalPanel, ColorPanel, HSLPanel, SplitToningPanel,
    CurvesPanel, DetailPanel, VignettePanel, CropPanel,
)
from .widgets.panels.base_panel import CollapsibleSection


class ParamUndoCommand(QUndoCommand):
    def __init__(self, window: 'MainWindow', old_params: dict, new_params: dict):
        super().__init__("Edit")
        self._window = window
        self._old = old_params
        self._new = new_params

    def undo(self):
        self._window._apply_params_snapshot(self._old)

    def redo(self):
        self._window._apply_params_snapshot(self._new)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChromaForge — No Image")
        self.resize(1400, 900)

        self._original: np.ndarray | None = None
        self._preview: np.ndarray | None = None
        self._processed: np.ndarray | None = None
        self._current_path: Path | None = None
        self._sidecar: Sidecar | None = None
        self._before_after: bool = False
        self._undo_stack = QUndoStack(self)
        self._last_committed_params: dict = {}
        self._edit_in_progress: bool = False
        self._undo_redo_in_progress: bool = False

        self._worker = PipelineThread(self)
        self._worker.resultReady.connect(self._on_processed)

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(50)
        self._debounce.timeout.connect(self._request_process)

        self._setup_ui()
        self._setup_undo_redo()
        self._setup_menu()
        self._setup_toolbar()
        self._load_stylesheet()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self._viewer = ImageViewer()
        center_layout.addWidget(self._viewer, 1)

        self._histogram = HistogramWidget()
        center_layout.addWidget(self._histogram)
        splitter.addWidget(center_panel)

        right_panel = QWidget()
        right_panel.setObjectName("panelContainer")
        right_panel.setFixedWidth(280)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._tonal = TonalPanel()
        self._tonal.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Tonal", self._tonal, collapsed=False))

        self._color = ColorPanel()
        self._color.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Color", self._color, collapsed=True))

        self._hsl = HSLPanel()
        self._hsl.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("HSL", self._hsl, collapsed=True))

        self._split_toning = SplitToningPanel()
        self._split_toning.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Split Toning", self._split_toning, collapsed=True))

        self._curves = CurvesPanel()
        self._curves.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Curves", self._curves, collapsed=True))

        self._detail = DetailPanel()
        self._detail.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Detail", self._detail, collapsed=True))

        self._vignette = VignettePanel()
        self._vignette.paramsChanged.connect(self._on_params_changed)
        right_layout.addWidget(CollapsibleSection("Vignette", self._vignette, collapsed=True))

        self._crop = CropPanel()
        self._crop.paramsChanged.connect(self._on_params_changed)
        self._crop.cropEnabled.connect(self._viewer.set_crop_mode)
        self._viewer.cropRectChanged.connect(self._on_crop_rect_changed)
        right_layout.addWidget(CollapsibleSection("Crop", self._crop, collapsed=True))

        right_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(right_panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        splitter.addWidget(scroll)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel("No image loaded")
        self._status.addWidget(self._status_label)

    def _setup_undo_redo(self):
        self._undo_redo_in_progress = False
        self._undo_action = self._undo_stack.createUndoAction(self, "&Undo")
        self._undo_action.setShortcut("Ctrl+Z")
        self._redo_action = self._undo_stack.createRedoAction(self, "&Redo")
        self._redo_action.setShortcut("Ctrl+Shift+Z")

    def _setup_menu(self):
        menubar = self.menuBar()
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)
        edit_menu.addSeparator()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._action("&Open...", "Ctrl+O", self._open_file))

        self._export_action = self._action("&Export...", "Ctrl+Shift+E", self._export_file)
        self._export_action.setEnabled(False)
        file_menu.addAction(self._export_action)
        file_menu.addSeparator()
        file_menu.addAction(self._action("E&xit", "Ctrl+Q", self.close))

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._action("&Fit to Window", "Ctrl+0", self._viewer.fit_image))
        view_menu.addAction(self._action("Zoom &In", "Ctrl++", self._viewer.zoom_in))
        view_menu.addAction(self._action("Zoom &Out", "Ctrl+-", self._viewer.zoom_out))
        view_menu.addSeparator()
        self._ba_action = self._action("&Before/After", "\\", self._toggle_before_after)
        self._ba_action.setCheckable(True)
        view_menu.addAction(self._ba_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        toolbar.addAction(self._undo_action)
        toolbar.addAction(self._redo_action)
        toolbar.addSeparator()
        self._ba_btn = toolbar.addAction("B/A")
        self._ba_btn.setCheckable(True)
        self._ba_btn.triggered.connect(self._toggle_before_after)

    def _action(self, text: str, shortcut: str, slot):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(shortcut)
        if slot:
            a.triggered.connect(slot)
        return a

    def _load_stylesheet(self):
        qss_path = Path(__file__).parent / "resources" / "style.qss"
        if qss_path.exists():
            with open(qss_path) as f:
                self.setStyleSheet(f.read())

    def _open_file(self):
        self._save_current_sidecar()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.dng *.cr2 *.cr3 *.nef *.arw *.raf *.orf *.rw2 *.pef *.raw);;All Files (*)"
        )
        if not path:
            return

        img = load_image(path)
        if img is None:
            QMessageBox.warning(self, "Error", f"Could not load: {path}")
            return

        self._current_path = Path(path)
        self._original = img
        self._preview = compute_downsampled(img)
        self.setWindowTitle(f"ChromaForge — {self._current_path.name}")
        self._status_label.setText(f"{self._current_path.name} — {img.shape[1]}\u00d7{img.shape[0]}")

        sidecar = load_sidecar(self._current_path)
        if sidecar:
            self._sidecar = sidecar
            self._apply_sidecar_to_panels()
        else:
            self._sidecar = Sidecar(sourceFile=self._current_path.name)

        self._before_after = False
        self._ba_action.setChecked(False)
        self._ba_btn.setChecked(False)
        self._export_action.setEnabled(True)
        self._undo_stack.clear()
        self._edit_in_progress = False
        self._last_committed_params = {}
        self._worker.set_input(self._preview)
        self._request_process()

    def _save_current_sidecar(self):
        if self._current_path is None or self._sidecar is None:
            return
        self._sync_sidecar_from_panels()
        save_sidecar(self._current_path, self._sidecar)

    def _sync_sidecar_from_panels(self):
        if self._sidecar is None:
            return
        t = self._tonal.get_params()
        c = self._color.get_params()
        s = self._sidecar.edits
        s.tonal.exposure = t.get("exposure", {}).get("stops", 0.0)
        s.tonal.contrast = t.get("contrast", {}).get("amount", 0.0)
        s.tonal.highlights = t.get("highlights", {}).get("amount", 0.0)
        s.tonal.shadows = t.get("shadows", {}).get("amount", 0.0)
        s.tonal.whites = t.get("whites", {}).get("amount", 0.0)
        s.tonal.blacks = t.get("blacks", {}).get("amount", 0.0)
        s.tonal.brightness = t.get("brightness", {}).get("amount", 0.0)
        s.color.saturation = c.get("saturation", {}).get("amount", 0.0)
        s.color.vibrance = c.get("vibrance", {}).get("amount", 0.0)
        wb = c.get("whiteBalance", {})
        s.whiteBalance.temperature = wb.get("temperature", 0.0)
        s.whiteBalance.tint = wb.get("tint", 0.0)
        s.color.hue = c.get("hue", {}).get("degrees", 0.0)

        hsl = self._hsl.get_params().get("hsl", {})
        for band_name in constants.HSL_BAND_NAMES:
            band = hsl.get(band_name, {})
            getattr(s.hsl, band_name).hue = band.get("hue", 0)
            getattr(s.hsl, band_name).saturation = band.get("saturation", 0)
            getattr(s.hsl, band_name).luminance = band.get("luminance", 0)

        st = self._split_toning.get_params().get("splitToning", {})
        s.splitToning.shadowHue = st.get("shadowHue", 0)
        s.splitToning.shadowSat = st.get("shadowSat", 0)
        s.splitToning.highlightHue = st.get("highlightHue", 0)
        s.splitToning.highlightSat = st.get("highlightSat", 0)
        s.splitToning.balance = st.get("balance", 0)

        curves = self._curves.get_params().get("curves", {})
        s.curves.master = curves.get("master", [])
        s.curves.red = curves.get("red", [])
        s.curves.blue = curves.get("blue", [])
        s.curves.green = curves.get("green", [])

        det = self._detail.get_params()
        s.detail.sharpenAmount = det.get("sharpening", {}).get("amount", 0)
        s.detail.sharpenRadius = det.get("sharpening", {}).get("radius", 1.0)
        s.detail.noiseLuminance = det.get("noiseReduction", {}).get("luminance", 0)
        s.detail.noiseColor = det.get("noiseReduction", {}).get("color", 0)

        vig = self._vignette.get_params().get("vignette", {})
        s.vignette.amount = vig.get("amount", 0)
        s.vignette.midpoint = vig.get("midpoint", 50)
        s.vignette.roundness = vig.get("roundness", 0)
        s.vignette.feather = vig.get("feather", 50)

        cr = self._crop.get_params().get("cropRotate", {})
        s.geometry.crop = cr.get("crop")
        s.geometry.rotationDegrees = cr.get("rotationDegrees", 0)
        s.geometry.flipH = cr.get("flipH", False)
        s.geometry.flipV = cr.get("flipV", False)

    def _apply_sidecar_to_panels(self):
        if self._sidecar is None:
            return
        t = self._sidecar.edits.tonal
        self._tonal.set_values(
            exposure=t.exposure, contrast=t.contrast, highlights=t.highlights,
            shadows=t.shadows, whites=t.whites, blacks=t.blacks, brightness=t.brightness,
        )
        co = self._sidecar.edits.color
        wb = self._sidecar.edits.whiteBalance
        self._color.set_values(
            saturation=co.saturation, vibrance=co.vibrance,
            temperature=wb.temperature, tint=wb.tint, hue=co.hue,
        )
        hsl_sc = self._sidecar.edits.hsl
        self._hsl.set_params({
            name: {
                "hue": getattr(hsl_sc, name).hue,
                "saturation": getattr(hsl_sc, name).saturation,
                "luminance": getattr(hsl_sc, name).luminance,
            }
            for name in constants.HSL_BAND_NAMES
        })
        st_sc = self._sidecar.edits.splitToning
        self._split_toning.set_values(
            shadowHue=st_sc.shadowHue, shadowSat=st_sc.shadowSat,
            highlightHue=st_sc.highlightHue, highlightSat=st_sc.highlightSat,
            balance=st_sc.balance,
        )
        cv = self._sidecar.edits.curves
        self._curves.set_curves(
            master=cv.master if cv.master else None,
            red=cv.red if cv.red else None,
            green=cv.green if cv.green else None,
            blue=cv.blue if cv.blue else None,
        )
        det_sc = self._sidecar.edits.detail
        self._detail.set_values(
            sharpen_amount=det_sc.sharpenAmount, sharpen_radius=det_sc.sharpenRadius,
            nr_luminance=det_sc.noiseLuminance, nr_color=det_sc.noiseColor,
        )
        vig_sc = self._sidecar.edits.vignette
        self._vignette.set_values(
            amount=vig_sc.amount, midpoint=vig_sc.midpoint,
            roundness=vig_sc.roundness, feather=vig_sc.feather,
        )
        geo = self._sidecar.edits.geometry
        self._crop.set_values(
            crop=geo.crop, rotationDegrees=geo.rotationDegrees,
            flipH=geo.flipH, flipV=geo.flipV,
        )
        self._update_crop_overlay()

    def _update_crop_overlay(self):
        cp = self._crop.get_params().get("cropRotate", {})
        crop = cp.get("crop")
        if crop and len(crop) == 4:
            self._viewer.update_crop_overlay(*crop)
        else:
            self._viewer.update_crop_overlay(0.0, 0.0, 1.0, 1.0)

    def _on_crop_rect_changed(self, left: float, top: float, right: float, bottom: float):
        self._crop.set_values(crop=[left, top, right, bottom])
        self._crop._emit_params()

    def _on_params_changed(self):
        if self._undo_redo_in_progress:
            return
        if not self._edit_in_progress:
            self._edit_in_progress = True
            self._last_committed_params = self._collect_params()
        self._debounce.start()

    def _request_process(self):
        if self._preview is None:
            return
        if self._edit_in_progress and not self._undo_redo_in_progress:
            self._edit_in_progress = False
            current = self._collect_params()
            if current != self._last_committed_params:
                cmd = ParamUndoCommand(self, self._last_committed_params, current)
                self._undo_stack.push(cmd)
                self._last_committed_params = current
        self._worker.set_params(self._collect_params())
        self._worker.request_process()

    def _collect_params(self) -> dict:
        params = {}
        params.update(self._tonal.get_params())
        params.update(self._color.get_params())
        params.update(self._hsl.get_params())
        params.update(self._split_toning.get_params())
        params.update(self._curves.get_params())
        params.update(self._detail.get_params())
        params.update(self._vignette.get_params())
        params.update(self._crop.get_params())
        return params

    def _on_processed(self, result: np.ndarray):
        self._processed = result
        if not self._before_after:
            self._viewer.set_image(result)
            self._histogram.set_from_image(result)

    def _apply_params_snapshot(self, params: dict):
        self._undo_redo_in_progress = True

        t = params.get("tonal", {})
        self._tonal.set_values(
            exposure=t.get("exposure", {}).get("stops", 0.0),
            contrast=t.get("contrast", {}).get("amount", 0.0),
            highlights=t.get("highlights", {}).get("amount", 0.0),
            shadows=t.get("shadows", {}).get("amount", 0.0),
            whites=t.get("whites", {}).get("amount", 0.0),
            blacks=t.get("blacks", {}).get("amount", 0.0),
            brightness=t.get("brightness", {}).get("amount", 0.0),
        )

        c = params.get("color", {})
        wb = c.get("whiteBalance", {})
        self._color.set_values(
            saturation=c.get("saturation", {}).get("amount", 0.0),
            vibrance=c.get("vibrance", {}).get("amount", 0.0),
            temperature=wb.get("temperature", 0.0),
            tint=wb.get("tint", 0.0),
            hue=c.get("hue", {}).get("degrees", 0.0),
        )

        hsl = params.get("hsl", {}).get("hsl", {})
        self._hsl.set_params(hsl)

        st = params.get("splitToning", {}).get("splitToning", {})
        self._split_toning.set_values(
            shadowHue=st.get("shadowHue", 0),
            shadowSat=st.get("shadowSat", 0),
            highlightHue=st.get("highlightHue", 0),
            highlightSat=st.get("highlightSat", 0),
            balance=st.get("balance", 0),
        )

        cv = params.get("curves", {}).get("curves", {})
        self._curves.set_curves(
            master=cv.get("master"),
            red=cv.get("red"),
            green=cv.get("green"),
            blue=cv.get("blue"),
        )

        det = params.get("detail", {})
        sh = det.get("sharpening", {})
        nr = det.get("noiseReduction", {})
        self._detail.set_values(
            sharpen_amount=sh.get("amount", 0),
            sharpen_radius=sh.get("radius", 1.0),
            nr_luminance=nr.get("luminance", 0),
            nr_color=nr.get("color", 0),
        )

        vig = params.get("vignette", {}).get("vignette", {})
        self._vignette.set_values(
            amount=vig.get("amount", 0),
            midpoint=vig.get("midpoint", 50),
            roundness=vig.get("roundness", 0),
            feather=vig.get("feather", 50),
        )

        cr = params.get("cropRotate", {})
        self._crop.set_values(
            crop=cr.get("crop"),
            rotationDegrees=cr.get("rotationDegrees", 0),
            flipH=cr.get("flipH", False),
            flipV=cr.get("flipV", False),
        )
        self._update_crop_overlay()

        self._last_committed_params = self._collect_params()
        self._undo_redo_in_progress = False
        self._request_process()

    def _toggle_before_after(self):
        if self._preview is None:
            return
        self._before_after = not self._before_after
        self._ba_action.setChecked(self._before_after)
        self._ba_btn.setChecked(self._before_after)
        if self._before_after:
            self._viewer.set_image(self._preview)
            self._histogram.set_from_image(self._preview)
        elif self._processed is not None:
            self._viewer.set_image(self._processed)
            self._histogram.set_from_image(self._processed)

    def _export_file(self):
        if self._original is None or self._current_path is None:
            return
        dlg = ExportDialog(self._current_path.name, self)
        if dlg.exec() != ExportDialog.DialogCode.Accepted:
            return
        result = dlg.get_result()
        out_path = result["path"]
        quality = result["quality"]
        fmt = result["format"]

        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Processing full-size export...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        QApplication.processEvents()

        from .core.pipeline import ProcessingPipeline
        import cv2
        pipe = ProcessingPipeline()
        pipe.set_params(self._collect_params())
        full_res = pipe.apply(self._original)

        uint8_img = (np.clip(full_res, 0.0, 1.0) * 255).astype(np.uint8)
        bgr = cv2.cvtColor(uint8_img, cv2.COLOR_RGB2BGR)
        params = []
        if fmt == "JPEG":
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif fmt == "PNG":
            params = [cv2.IMWRITE_PNG_COMPRESSION, 9 - quality // 11]
        ok = cv2.imwrite(out_path, bgr, params)
        progress.close()
        if ok:
            self._status_label.setText(f"Exported to {Path(out_path).name}")
        else:
            QMessageBox.warning(self, "Export Error", f"Failed to write {out_path}")

    def closeEvent(self, event):
        self._save_current_sidecar()
        self._worker.stop()
        super().closeEvent(event)
