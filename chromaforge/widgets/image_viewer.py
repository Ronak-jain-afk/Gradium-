import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, Signal, QRectF
from ..core import array_to_qimage


OVERLAY_COLOR = QColor(0, 0, 0, 140)


class _CropRectItem(QGraphicsRectItem):
    resized = Signal(QRectF)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dragging = False
        self._drag_edge = 0  # bitmask: 1=left, 2=top, 4=right, 8=bottom

    def set_rect_from_norm(self, norm_rect: tuple[float, float, float, float], img_w: float, img_h: float):
        l, t, r, b = norm_rect
        self.setRect(QRectF(l * img_w, t * img_h, (r - l) * img_w, (b - t) * img_h))


class ImageViewer(QGraphicsView):
    cropRectChanged = Signal(float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self._crop_mode = False
        self._crop_drag: QGraphicsRectItem | None = None
        self._crop_origin: tuple[float, float] | None = None
        self._overlay_items: list[QGraphicsRectItem] = []
        self._crop_border: QGraphicsRectItem | None = None

        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._zoom = 0

    def set_image(self, img: np.ndarray):
        qimg = array_to_qimage(img)
        pixmap = QPixmap.fromImage(qimg)
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect())
        self.fit_image()

    def fit_image(self):
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = 0

    def zoom_in(self):
        self._zoom += 1
        self._apply_zoom()

    def zoom_out(self):
        self._zoom -= 1
        self._apply_zoom()

    def _apply_zoom(self):
        factor = 1.25 ** self._zoom
        tr = self.transform()
        tr.reset()
        tr.scale(factor, factor)
        self.setTransform(tr)

    # --- Crop mode ---

    def set_crop_mode(self, active: bool):
        self._crop_mode = active
        self.setDragMode(QGraphicsView.DragMode.NoDrag if active else QGraphicsView.DragMode.ScrollHandDrag)
        if not active:
            self._clear_crop_overlay()

    def update_crop_overlay(self, left: float, top: float, right: float, bottom: float):
        self._clear_crop_overlay()
        if not self._pixmap_item.pixmap() or self._pixmap_item.pixmap().isNull():
            return
        r = self._pixmap_item.pixmap().rect()
        img_w, img_h = r.width(), r.height()
        if right <= left or bottom <= top:
            return

        crop_rect = QRectF(left * img_w, top * img_h, (right - left) * img_w, (bottom - top) * img_h)
        dark = QBrush(OVERLAY_COLOR)
        no_brush = QBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)

        # Four overlay rects: top, left, right, bottom
        top_r = QGraphicsRectItem(0, 0, img_w, crop_rect.top())
        top_r.setBrush(dark)
        top_r.setPen(no_brush)
        self._overlay_items.append(top_r)
        self._scene.addItem(top_r)

        left_r = QGraphicsRectItem(0, crop_rect.top(), crop_rect.left(), crop_rect.height())
        left_r.setBrush(dark)
        left_r.setPen(no_brush)
        self._overlay_items.append(left_r)
        self._scene.addItem(left_r)

        right_r = QGraphicsRectItem(crop_rect.right(), crop_rect.top(), img_w - crop_rect.right(), crop_rect.height())
        right_r.setBrush(dark)
        right_r.setPen(no_brush)
        self._overlay_items.append(right_r)
        self._scene.addItem(right_r)

        bottom_r = QGraphicsRectItem(0, crop_rect.bottom(), img_w, img_h - crop_rect.bottom())
        bottom_r.setBrush(dark)
        bottom_r.setPen(no_brush)
        self._overlay_items.append(bottom_r)
        self._scene.addItem(bottom_r)

        self._crop_border = QGraphicsRectItem(crop_rect)
        self._crop_border.setBrush(no_brush)
        self._crop_border.setPen(pen)
        self._scene.addItem(self._crop_border)

    def _clear_crop_overlay(self):
        for item in self._overlay_items:
            self._scene.removeItem(item)
        self._overlay_items.clear()
        if self._crop_border:
            self._scene.removeItem(self._crop_border)
            self._crop_border = None

    def mousePressEvent(self, event):
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.pos())
            self._crop_origin = (sp.x(), sp.y())
            pen = QPen(QColor(255, 255, 255, 200))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(2)
            self._crop_drag = QGraphicsRectItem()
            self._crop_drag.setPen(pen)
            self._crop_drag.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self._scene.addItem(self._crop_drag)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._crop_drag and self._crop_origin:
            sp = self.mapToScene(event.pos())
            x1, y1 = self._crop_origin
            x2, y2 = sp.x(), sp.y()
            rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            self._crop_drag.setRect(rect)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._crop_drag and self._crop_origin and event.button() == Qt.MouseButton.LeftButton:
            self._scene.removeItem(self._crop_drag)
            self._crop_drag = None
            sp = self.mapToScene(event.pos())
            if not self._pixmap_item.pixmap():
                event.accept()
                return
            r = self._pixmap_item.pixmap().rect()
            img_w, img_h = r.width(), r.height()
            if img_w == 0 or img_h == 0:
                event.accept()
                return
            x1, y1 = self._crop_origin
            x2, y2 = sp.x(), sp.y()
            l = max(0.0, min(x1, x2)) / img_w
            t = max(0.0, min(y1, y2)) / img_h
            rb = min(img_w, max(x1, x2)) / img_w
            bb = min(img_h, max(y1, y2)) / img_h
            self._crop_origin = None
            if rb - l > 0.01 and bb - t > 0.01:
                self.cropRectChanged.emit(l, t, rb, bb)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap_item.pixmap() and not self._pixmap_item.pixmap().isNull():
            self.fit_image()
