from __future__ import annotations
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PySide6.QtCore import Qt, QPointF, Signal, QRectF, QTimer
from ..core.curves import Point, evaluate_curve


_PADDING = 20
_POINT_RADIUS = 5
_GRID_COLOR = QColor(60, 58, 55)
_DIAG_COLOR = QColor(80, 78, 74)
_CURVE_COLOR = QColor(212, 148, 62)
_POINT_COLOR = QColor(212, 148, 62)
_POINT_FILL = QColor(28, 27, 25)
_HOVER_COLOR = QColor(232, 168, 76)
_AXIS_COLOR = QColor(100, 98, 94)


class CurveWidget(QWidget):
    pointsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

        self._points: list[Point] = [(0.0, 0.0), (1.0, 1.0)]
        self._selected: int = -1
        self._hovered: int = -1
        self._dragging: int = -1
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(250)
        self._click_timer.timeout.connect(self._on_click_timeout)
        self._click_pos = QPointF()

    def set_points(self, points: list[Point]):
        self._points = points.copy()
        self._selected = -1
        self._hovered = -1
        self.update()

    def get_points(self) -> list[Point]:
        return self._points.copy()

    def _to_widget(self, x: float, y: float) -> QPointF:
        rect = self._plot_rect()
        return QPointF(rect.left() + x * rect.width(), rect.bottom() - y * rect.height())

    def _to_data(self, pos: QPointF) -> tuple[float, float]:
        rect = self._plot_rect()
        x = (pos.x() - rect.left()) / rect.width()
        y = (rect.bottom() - pos.y()) / rect.height()
        return (np.clip(x, 0.0, 1.0), np.clip(y, 0.0, 1.0))

    def _plot_rect(self) -> QRectF:
        return QRectF(_PADDING, _PADDING, self.width() - 2 * _PADDING, self.height() - 2 * _PADDING)

    def _hit_test(self, pos: QPointF) -> int:
        for i, (px, py) in enumerate(self._points):
            wp = self._to_widget(px, py)
            if (pos - wp).manhattanLength() < _POINT_RADIUS + 4:
                return i
        return -1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._plot_rect()

        # Grid
        painter.setPen(QPen(_GRID_COLOR, 1))
        for v in [0.25, 0.5, 0.75]:
            x = rect.left() + v * rect.width()
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            y = rect.bottom() - v * rect.height()
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        # Axes box
        painter.setPen(QPen(_AXIS_COLOR, 1))
        painter.drawRect(rect)

        # Diagonal reference
        painter.setPen(QPen(_DIAG_COLOR, 1, Qt.PenStyle.DashLine))
        painter.drawLine(self._to_widget(0, 0), self._to_widget(1, 1))

        # Curve
        if len(self._points) >= 2:
            lut = evaluate_curve(self._points, max(rect.width(), 64))
            path = QPainterPath()
            first = True
            for i, val in enumerate(lut):
                x = rect.left() + (i / (len(lut) - 1)) * rect.width()
                y = rect.bottom() - val * rect.height()
                if first:
                    path.moveTo(QPointF(x, y))
                    first = False
                else:
                    path.lineTo(QPointF(x, y))
            painter.setPen(QPen(_CURVE_COLOR, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Points
        for i, (px, py) in enumerate(self._points):
            wp = self._to_widget(px, py)
            is_sel = i == self._selected or i == self._hovered
            painter.setPen(QPen(_HOVER_COLOR if is_sel else _POINT_COLOR, 2))
            painter.setBrush(QBrush(_POINT_FILL))
            painter.drawEllipse(wp, _POINT_RADIUS, _POINT_RADIUS)
            if is_sel:
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawEllipse(wp, _POINT_RADIUS + 3, _POINT_RADIUS + 3)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        idx = self._hit_test(event.position())
        if idx >= 0:
            self._selected = idx
            self._dragging = idx
            self._click_timer.stop()
        else:
            self._selected = -1
            # Wait for double-click timer
            self._click_pos = event.position()
            self._click_timer.start()
        self.update()

    def _on_click_timeout(self):
        # Single click on empty space → add point
        x, y = self._to_data(self._click_pos)
        insert_pos = next((i for i, p in enumerate(self._points) if p[0] >= x), len(self._points))
        self._points.insert(insert_pos, (round(x, 3), round(y, 3)))
        self._selected = insert_pos
        self.pointsChanged.emit()
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        idx = self._hit_test(pos)
        self._hovered = idx
        self.setCursor(Qt.CursorShape.ArrowCursor if idx >= 0 else Qt.CursorShape.CrossCursor)

        if self._dragging >= 0:
            x, y = self._to_data(pos)
            pts = self._points
            i = self._dragging
            x_min = pts[i - 1][0] + 0.01 if i > 0 else 0.0
            x_max = pts[i + 1][0] - 0.01 if i < len(pts) - 1 else 1.0
            self._points[i] = (round(max(x_min, min(x, x_max)), 3), round(y, 3))
            self.pointsChanged.emit()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self._selected >= 0:
            if 0 < self._selected < len(self._points) - 1:
                del self._points[self._selected]
                self._selected = -1
                self.pointsChanged.emit()
        self._dragging = -1
        self.update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self._click_timer.stop()
        idx = self._hit_test(event.position())
        if 0 < idx < len(self._points) - 1:
            del self._points[idx]
            self._selected = -1
            self.pointsChanged.emit()
        self.update()
        super().mouseDoubleClickEvent(event)
