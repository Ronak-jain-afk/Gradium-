from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class DetailPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        sh = QLabel("Sharpen")
        sh.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(sh)

        self._sharpen_amount = SliderRow("Amount", constants.SHARPEN_AMOUNT_DEFAULT,
                                         constants.SHARPEN_AMOUNT_MIN, constants.SHARPEN_AMOUNT_MAX,
                                         constants.SHARPEN_AMOUNT_STEP)
        layout.addWidget(self._sharpen_amount)

        self._sharpen_radius = SliderRow("Radius", constants.SHARPEN_RADIUS_DEFAULT,
                                         constants.SHARPEN_RADIUS_MIN, constants.SHARPEN_RADIUS_MAX,
                                         constants.SHARPEN_RADIUS_STEP)
        layout.addWidget(self._sharpen_radius)

        nr = QLabel("Noise Reduction")
        nr.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(nr)

        self._nr_luminance = SliderRow("Luminance", constants.NR_LUMINANCE_DEFAULT,
                                       constants.NR_LUMINANCE_MIN, constants.NR_LUMINANCE_MAX,
                                       constants.NR_LUMINANCE_STEP)
        layout.addWidget(self._nr_luminance)

        self._nr_color = SliderRow("Color", constants.NR_COLOR_DEFAULT,
                                   constants.NR_COLOR_MIN, constants.NR_COLOR_MAX,
                                   constants.NR_COLOR_STEP)
        layout.addWidget(self._nr_color)

        for s in [self._sharpen_amount, self._sharpen_radius,
                  self._nr_luminance, self._nr_color]:
            s.valueChanged.connect(self._emit_params)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {
            "sharpening": {"amount": self._sharpen_amount.value(), "radius": self._sharpen_radius.value()},
            "noiseReduction": {"luminance": self._nr_luminance.value(), "color": self._nr_color.value()},
        }

    def set_values(self, sharpen_amount=0.0, sharpen_radius=1.0, nr_luminance=0.0, nr_color=0.0):
        self._sharpen_amount.set_value(sharpen_amount)
        self._sharpen_radius.set_value(sharpen_radius)
        self._nr_luminance.set_value(nr_luminance)
        self._nr_color.set_value(nr_color)
