from pathlib import Path

import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QLabel, QMessageBox, QSplitter, QStatusBar,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from .core import (
    load_image, compute_downsampled, PipelineThread,
    Sidecar, load_sidecar, save_sidecar, constants,
)
from .widgets import ImageViewer, HistogramWidget
from .widgets.panels import TonalPanel, ColorPanel, HSLPanel, SplitToningPanel
from .widgets.panels.base_panel import CollapsibleSection


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChromaForge — No Image")
        self.resize(1400, 900)

        self._original: np.ndarray | None = None
        self._preview: np.ndarray | None = None
        self._current_path: Path | None = None
        self._sidecar: Sidecar | None = None

        self._worker = PipelineThread(self)
        self._worker.resultReady.connect(self._on_processed)

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(50)
        self._debounce.timeout.connect(self._request_process)

        self._setup_ui()
        self._setup_menu()
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

        for title in ["Curves", "Detail", "Vignette", "Crop"]:
            placeholder = QLabel(f"{title} controls coming soon")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #6a6865; padding: 16px; font-size: 11px;")
            right_layout.addWidget(CollapsibleSection(title, placeholder, collapsed=True))

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

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._action("&Open...", "Ctrl+O", self._open_file))

        self._export_action = self._action("&Export...", "Ctrl+Shift+E", None)
        self._export_action.setEnabled(False)
        file_menu.addAction(self._export_action)
        file_menu.addSeparator()
        file_menu.addAction(self._action("E&xit", "Ctrl+Q", self.close))

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._action("&Fit to Window", "Ctrl+0", self._viewer.fit_image))
        view_menu.addAction(self._action("Zoom &In", "Ctrl++", self._viewer.zoom_in))
        view_menu.addAction(self._action("Zoom &Out", "Ctrl+-", self._viewer.zoom_out))

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
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.bmp);;All Files (*)"
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

    def _on_params_changed(self):
        self._debounce.start()

    def _request_process(self):
        if self._preview is None:
            return
        self._worker.set_params(self._collect_params())
        self._worker.request_process()

    def _collect_params(self) -> dict:
        params = {}
        params.update(self._tonal.get_params())
        params.update(self._color.get_params())
        params.update(self._hsl.get_params())
        params.update(self._split_toning.get_params())
        return params

    def _on_processed(self, result: np.ndarray):
        self._viewer.set_image(result)
        self._histogram.set_from_image(result)

    def closeEvent(self, event):
        self._save_current_sidecar()
        self._worker.stop()
        super().closeEvent(event)
