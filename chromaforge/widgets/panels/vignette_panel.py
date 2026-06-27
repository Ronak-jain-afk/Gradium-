from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ..slider_row import SliderRow
from ...core import constants


class VignettePanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._amount = SliderRow("Amount", constants.VIGNETTE_AMOUNT_DEFAULT,
                                 constants.VIGNETTE_AMOUNT_MIN, constants.VIGNETTE_AMOUNT_MAX,
                                 constants.VIGNETTE_AMOUNT_STEP)
        layout.addWidget(self._amount)

        self._midpoint = SliderRow("Midpoint", constants.VIGNETTE_MIDPOINT_DEFAULT,
                                   constants.VIGNETTE_MIDPOINT_MIN, constants.VIGNETTE_MIDPOINT_MAX,
                                   constants.VIGNETTE_MIDPOINT_STEP)
        layout.addWidget(self._midpoint)

        self._roundness = SliderRow("Roundness", constants.VIGNETTE_ROUNDNESS_DEFAULT,
                                    constants.VIGNETTE_ROUNDNESS_MIN, constants.VIGNETTE_ROUNDNESS_MAX,
                                    constants.VIGNETTE_ROUNDNESS_STEP)
        layout.addWidget(self._roundness)

        self._feather = SliderRow("Feather", constants.VIGNETTE_FEATHER_DEFAULT,
                                  constants.VIGNETTE_FEATHER_MIN, constants.VIGNETTE_FEATHER_MAX,
                                  constants.VIGNETTE_FEATHER_STEP)
        layout.addWidget(self._feather)

        for s in [self._amount, self._midpoint, self._roundness, self._feather]:
            s.valueChanged.connect(self._emit_params)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {
            "vignette": {
                "amount": self._amount.value(),
                "midpoint": self._midpoint.value(),
                "roundness": self._roundness.value(),
                "feather": self._feather.value(),
            }
        }

    def set_values(self, amount=0.0, midpoint=50.0, roundness=0.0, feather=50.0):
        self._amount.set_value(amount)
        self._midpoint.set_value(midpoint)
        self._roundness.set_value(roundness)
        self._feather.set_value(feather)
