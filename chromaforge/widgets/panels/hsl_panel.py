from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class _BandWidget(QWidget):
    changed = Signal()

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(2)

        self._hue = SliderRow("Hue", constants.HSL_DEFAULT, constants.HSL_MIN,
                              constants.HSL_MAX, constants.HSL_STEP)
        self._sat = SliderRow("Sat", constants.HSL_DEFAULT, constants.HSL_MIN,
                              constants.HSL_MAX, constants.HSL_STEP)
        self._lum = SliderRow("Lum", constants.HSL_DEFAULT, constants.HSL_MIN,
                              constants.HSL_MAX, constants.HSL_STEP)

        layout.addWidget(self._hue)
        layout.addWidget(self._sat)
        layout.addWidget(self._lum)

        self._hue.valueChanged.connect(self.changed)
        self._sat.valueChanged.connect(self.changed)
        self._lum.valueChanged.connect(self.changed)

    def get_params(self) -> dict:
        return {
            "hue": self._hue.value(),
            "saturation": self._sat.value(),
            "luminance": self._lum.value(),
        }

    def set_params(self, hue: float = 0, saturation: float = 0, luminance: float = 0):
        self._hue.set_value(hue)
        self._sat.set_value(saturation)
        self._lum.set_value(luminance)


class HSLPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._bands: dict[str, _BandWidget] = {}
        for name in constants.HSL_BAND_NAMES:
            band = _BandWidget(name.capitalize())
            band.changed.connect(self._emit_params)
            self._bands[name] = band
            layout.addWidget(band)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {"hsl": {name: band.get_params() for name, band in self._bands.items()}}

    def set_params(self, params: dict[str, dict]):
        for name, values in params.items():
            band = self._bands.get(name)
            if band:
                band.set_params(**values)
