from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class TonalPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._exposure = SliderRow("Exposure", constants.EXPOSURE_DEFAULT,
                                   constants.EXPOSURE_MIN, constants.EXPOSURE_MAX,
                                   constants.EXPOSURE_STEP)
        layout.addWidget(self._exposure)

        self._contrast = SliderRow("Contrast", constants.CONTRAST_DEFAULT,
                                   constants.CONTRAST_MIN, constants.CONTRAST_MAX,
                                   constants.CONTRAST_STEP)
        layout.addWidget(self._contrast)

        self._highlights = SliderRow("Highlights", constants.HIGHLIGHTS_DEFAULT,
                                     constants.HIGHLIGHTS_MIN, constants.HIGHLIGHTS_MAX,
                                     constants.HIGHLIGHTS_STEP)
        layout.addWidget(self._highlights)

        self._shadows = SliderRow("Shadows", constants.SHADOWS_DEFAULT,
                                  constants.SHADOWS_MIN, constants.SHADOWS_MAX,
                                  constants.SHADOWS_STEP)
        layout.addWidget(self._shadows)

        self._whites = SliderRow("Whites", constants.WHITES_DEFAULT,
                                 constants.WHITES_MIN, constants.WHITES_MAX,
                                 constants.WHITES_STEP)
        layout.addWidget(self._whites)

        self._blacks = SliderRow("Blacks", constants.BLACKS_DEFAULT,
                                 constants.BLACKS_MIN, constants.BLACKS_MAX,
                                 constants.BLACKS_STEP)
        layout.addWidget(self._blacks)

        self._brightness = SliderRow("Brightness", constants.BRIGHTNESS_DEFAULT,
                                     constants.BRIGHTNESS_MIN, constants.BRIGHTNESS_MAX,
                                     constants.BRIGHTNESS_STEP)
        layout.addWidget(self._brightness)

        for s in [self._exposure, self._contrast, self._highlights, self._shadows,
                  self._whites, self._blacks, self._brightness]:
            s.valueChanged.connect(self._emit_params)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {
            "exposure": {"stops": self._exposure.value()},
            "contrast": {"amount": self._contrast.value()},
            "highlights": {"amount": self._highlights.value()},
            "shadows": {"amount": self._shadows.value()},
            "whites": {"amount": self._whites.value()},
            "blacks": {"amount": self._blacks.value()},
            "brightness": {"amount": self._brightness.value()},
        }

    def set_values(self, **kwargs):
        for key, value in kwargs.items():
            slider = getattr(self, f"_{key}", None)
            if slider:
                slider.set_value(value)

    def reset(self):
        self._exposure.set_value(constants.EXPOSURE_DEFAULT)
        self._contrast.set_value(constants.CONTRAST_DEFAULT)
        self._highlights.set_value(constants.HIGHLIGHTS_DEFAULT)
        self._shadows.set_value(constants.SHADOWS_DEFAULT)
        self._whites.set_value(constants.WHITES_DEFAULT)
        self._blacks.set_value(constants.BLACKS_DEFAULT)
        self._brightness.set_value(constants.BRIGHTNESS_DEFAULT)
