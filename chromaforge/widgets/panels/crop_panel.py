from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class CropPanel(QWidget):
    paramsChanged = Signal(dict)
    cropEnabled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._crop_mode = QPushButton("Drag to Crop")
        self._crop_mode.setCheckable(True)
        self._crop_mode.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self._crop_mode.toggled.connect(self.cropEnabled)
        layout.addWidget(self._crop_mode)

        self._left = SliderRow("Left %", 0.0, 0.0, 100.0, 1.0)
        layout.addWidget(self._left)
        self._top = SliderRow("Top %", 0.0, 0.0, 100.0, 1.0)
        layout.addWidget(self._top)
        self._right = SliderRow("Right %", 100.0, 0.0, 100.0, 1.0)
        layout.addWidget(self._right)
        self._bottom = SliderRow("Bottom %", 100.0, 0.0, 100.0, 1.0)
        layout.addWidget(self._bottom)

        rst = QPushButton("Reset Crop")
        rst.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        rst.clicked.connect(self._reset_crop)
        layout.addWidget(rst)

        layout.addWidget(QLabel(""))  # spacer-like

        rot_label = QLabel("Rotation")
        rot_label.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(rot_label)

        rot_btns = QHBoxLayout()
        for text, val in [("\u21ba 90\u00b0 CCW", 270.0), ("\u21bb 90\u00b0 CW", 90.0)]:
            b = QPushButton(text)
            b.setStyleSheet("padding: 4px 8px; font-size: 11px;")
            b.clicked.connect(lambda _v=val: self._relative_rotate(_v))
            rot_btns.addWidget(b)
        layout.addLayout(rot_btns)

        self._straighten = SliderRow("Straighten", constants.ROTATION_DEFAULT,
                                     constants.ROTATION_MIN, constants.ROTATION_MAX,
                                     constants.ROTATION_STEP)
        layout.addWidget(self._straighten)

        flip_label = QLabel("Flip")
        flip_label.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(flip_label)

        flip_btns = QHBoxLayout()
        self._flip_h = QPushButton("H")
        self._flip_h.setCheckable(True)
        self._flip_h.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        flip_btns.addWidget(self._flip_h)
        self._flip_v = QPushButton("V")
        self._flip_v.setCheckable(True)
        self._flip_v.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        flip_btns.addWidget(self._flip_v)
        layout.addLayout(flip_btns)

        for s in [self._left, self._top, self._right, self._bottom, self._straighten]:
            s.valueChanged.connect(self._emit_params)
        self._flip_h.toggled.connect(self._emit_params)
        self._flip_v.toggled.connect(self._emit_params)

        layout.addStretch()

    def _reset_crop(self):
        self._left.set_value(0.0)
        self._top.set_value(0.0)
        self._right.set_value(100.0)
        self._bottom.set_value(100.0)
        self._emit_params()

    def _relative_rotate(self, degrees: float):
        current = self._straighten.value()
        self._straighten.set_value((current + degrees) % 360.0)
        self._emit_params()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        l = self._left.value() / 100.0
        t = self._top.value() / 100.0
        r = self._right.value() / 100.0
        b = self._bottom.value() / 100.0
        crop = None
        if l > 0.0 or t > 0.0 or r < 1.0 or b < 1.0:
            crop = [l, t, r, b]
        return {
            "cropRotate": {
                "crop": crop,
                "rotationDegrees": self._straighten.value(),
                "flipH": self._flip_h.isChecked(),
                "flipV": self._flip_v.isChecked(),
            }
        }

    def set_values(self, crop=None, rotationDegrees=0.0, flipH=False, flipV=False):
        if crop and len(crop) == 4:
            self._left.set_value(crop[0] * 100.0)
            self._top.set_value(crop[1] * 100.0)
            self._right.set_value(crop[2] * 100.0)
            self._bottom.set_value(crop[3] * 100.0)
        else:
            self._left.set_value(0.0)
            self._top.set_value(0.0)
            self._right.set_value(100.0)
            self._bottom.set_value(100.0)
        self._straighten.set_value(rotationDegrees)
        self._flip_h.setChecked(flipH)
        self._flip_v.setChecked(flipV)

    def reset_all(self):
        self._left.set_value(0.0)
        self._top.set_value(0.0)
        self._right.set_value(100.0)
        self._bottom.set_value(100.0)
        self._straighten.set_value(0.0)
        self._flip_h.setChecked(False)
        self._flip_v.setChecked(False)
        self._crop_mode.setChecked(False)
