import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QPointF


CHANNELS = {
    'r': QColor(220, 60, 60, 140),
    'g': QColor(60, 200, 60, 140),
    'b': QColor(60, 100, 220, 140),
}


class HistogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setMinimumWidth(200)
        self._histograms: dict[str, np.ndarray] = {}

    def set_from_image(self, img: np.ndarray):
        if img.size == 0:
            self._histograms = {}
            self.update()
            return

        uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
        h, w = img.shape[:2]
        pixel_count = h * w

        self._histograms = {}
        for i, ch in enumerate(['r', 'g', 'b']):
            hist = np.bincount(uint8[:, :, i].ravel(), minlength=256).astype(np.float32)
            if pixel_count > 0:
                hist /= pixel_count
            self._histograms[ch] = hist
        self.update()

    def paintEvent(self, event):
        if not self._histograms:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        for channel, color in CHANNELS.items():
            hist = self._histograms.get(channel)
            if hist is None:
                continue

            max_val = hist.max()
            if max_val == 0:
                continue

            path = QPainterPath()
            step = w / 256.0
            path.moveTo(QPointF(0.0, h))
            for i in range(256):
                x = i * step
                bar_h = (hist[i] / max_val) * h
                path.lineTo(QPointF(x, h - bar_h))
            path.lineTo(QPointF(w, h))
            path.closeSubpath()

            painter.fillPath(path, color)
