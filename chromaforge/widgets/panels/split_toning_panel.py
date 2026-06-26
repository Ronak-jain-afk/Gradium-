from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from ..slider_row import SliderRow
from ...core import constants


class SplitToningPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        sh = QLabel("Shadows")
        sh.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(sh)

        self._shadow_hue = SliderRow("Hue", constants.SPLIT_TONING_HUE_DEFAULT,
                                     constants.SPLIT_TONING_HUE_MIN, constants.SPLIT_TONING_HUE_MAX,
                                     constants.SPLIT_TONING_HUE_STEP)
        layout.addWidget(self._shadow_hue)

        self._shadow_sat = SliderRow("Sat", constants.SPLIT_TONING_SAT_DEFAULT,
                                     constants.SPLIT_TONING_SAT_MIN, constants.SPLIT_TONING_SAT_MAX,
                                     constants.SPLIT_TONING_SAT_STEP)
        layout.addWidget(self._shadow_sat)

        hl = QLabel("Highlights")
        hl.setStyleSheet("color: #b5b0a9; font-weight: 600; padding: 4px 0;")
        layout.addWidget(hl)

        self._highlight_hue = SliderRow("Hue", constants.SPLIT_TONING_HUE_DEFAULT,
                                        constants.SPLIT_TONING_HUE_MIN, constants.SPLIT_TONING_HUE_MAX,
                                        constants.SPLIT_TONING_HUE_STEP)
        layout.addWidget(self._highlight_hue)

        self._highlight_sat = SliderRow("Sat", constants.SPLIT_TONING_SAT_DEFAULT,
                                        constants.SPLIT_TONING_SAT_MIN, constants.SPLIT_TONING_SAT_MAX,
                                        constants.SPLIT_TONING_SAT_STEP)
        layout.addWidget(self._highlight_sat)

        self._balance = SliderRow("Balance", constants.SPLIT_TONING_BALANCE_DEFAULT,
                                  constants.SPLIT_TONING_BALANCE_MIN, constants.SPLIT_TONING_BALANCE_MAX,
                                  constants.SPLIT_TONING_BALANCE_STEP)
        layout.addWidget(self._balance)

        for s in [self._shadow_hue, self._shadow_sat, self._highlight_hue,
                  self._highlight_sat, self._balance]:
            s.valueChanged.connect(self._emit_params)

        layout.addStretch()

    def _emit_params(self):
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {
            "splitToning": {
                "shadowHue": self._shadow_hue.value(),
                "shadowSat": self._shadow_sat.value(),
                "highlightHue": self._highlight_hue.value(),
                "highlightSat": self._highlight_sat.value(),
                "balance": self._balance.value(),
            }
        }

    def set_values(self, shadowHue=0.0, shadowSat=0.0, highlightHue=0.0,
                   highlightSat=0.0, balance=0.0):
        self._shadow_hue.set_value(shadowHue)
        self._shadow_sat.set_value(shadowSat)
        self._highlight_hue.set_value(highlightHue)
        self._highlight_sat.set_value(highlightSat)
        self._balance.set_value(balance)
