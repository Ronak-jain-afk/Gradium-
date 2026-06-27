from PySide6.QtWidgets import QWidget, QHBoxLayout, QSlider, QLabel, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal


class SliderRow(QWidget):
    valueChanged = Signal(float)

    def __init__(self, label: str, default: float, min_val: float, max_val: float,
                 step: float, parent=None):
        super().__init__(parent)
        self._default = default
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setFixedWidth(70)
        layout.addWidget(self._label)

        self._spin = QDoubleSpinBox()
        self._spin.setRange(min_val, max_val)
        self._spin.setSingleStep(step)
        self._spin.setDecimals(2 if step < 1 else 1)
        self._spin.setValue(default)
        self._spin.setFixedWidth(65)
        layout.addWidget(self._spin)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 10000)
        self._slider.setValue(self._to_slider(default))
        layout.addWidget(self._slider, 1)

        self._slider.valueChanged.connect(self._on_slider)
        self._spin.valueChanged.connect(self._on_spin)

    def _to_slider(self, value: float) -> int:
        r = (self._spin.minimum(), self._spin.maximum())
        return int((value - r[0]) / (r[1] - r[0]) * 10000)

    def _from_slider(self, value: int) -> float:
        r = (self._spin.minimum(), self._spin.maximum())
        return r[0] + (value / 10000.0) * (r[1] - r[0])

    def _on_slider(self, value: int):
        real = self._from_slider(value)
        self._spin.blockSignals(True)
        self._spin.setValue(real)
        self._spin.blockSignals(False)
        self.valueChanged.emit(real)

    def _on_spin(self, value: float):
        self._slider.blockSignals(True)
        self._slider.setValue(self._to_slider(value))
        self._slider.blockSignals(False)
        self.valueChanged.emit(value)

    def mouseDoubleClickEvent(self, event):
        self._spin.setValue(self._default)
        super().mouseDoubleClickEvent(event)

    def value(self) -> float:
        return self._spin.value()

    def set_value(self, value: float):
        self._spin.setValue(value)
