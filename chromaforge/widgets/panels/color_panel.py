from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class ColorPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._saturation = SliderRow("Saturation", constants.SATURATION_DEFAULT,
                                     constants.SATURATION_MIN, constants.SATURATION_MAX,
                                     constants.SATURATION_STEP)
        layout.addWidget(self._saturation)

        self._vibrance = SliderRow("Vibrance", constants.VIBRANCE_DEFAULT,
                                   constants.VIBRANCE_MIN, constants.VIBRANCE_MAX,
                                   constants.VIBRANCE_STEP)
        layout.addWidget(self._vibrance)

        self._temperature = SliderRow("Temp", constants.TEMP_DEFAULT,
                                      constants.TEMP_MIN, constants.TEMP_MAX,
                                      constants.TEMP_STEP)
        layout.addWidget(self._temperature)

        self._tint = SliderRow("Tint", constants.TINT_DEFAULT,
                               constants.TINT_MIN, constants.TINT_MAX,
                               constants.TINT_STEP)
        layout.addWidget(self._tint)

        self._hue = SliderRow("Hue", constants.HUE_DEFAULT,
                              constants.HUE_MIN, constants.HUE_MAX,
                              constants.HUE_STEP)
        layout.addWidget(self._hue)

        for s in [self._saturation, self._vibrance, self._temperature,
                  self._tint, self._hue]:
            s.valueChanged.connect(self._emit_params)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {
            "saturation": {"amount": self._saturation.value()},
            "vibrance": {"amount": self._vibrance.value()},
            "whiteBalance": {
                "temperature": self._temperature.value(),
                "tint": self._tint.value(),
            },
            "hue": {"degrees": self._hue.value()},
        }

    def set_values(self, **kwargs):
        for key, value in kwargs.items():
            slider = getattr(self, f"_{key}", None)
            if slider:
                slider.set_value(value)

    def reset(self):
        self._saturation.set_value(constants.SATURATION_DEFAULT)
        self._vibrance.set_value(constants.VIBRANCE_DEFAULT)
        self._temperature.set_value(constants.TEMP_DEFAULT)
        self._tint.set_value(constants.TINT_DEFAULT)
        self._hue.set_value(constants.HUE_DEFAULT)
