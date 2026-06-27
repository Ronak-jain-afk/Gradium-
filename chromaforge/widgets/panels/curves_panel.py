from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt
from ..curve_widget import CurveWidget
from ...core.curves import Point, default_curve


_CHANNEL_NAMES = {"master": "Master", "red": "R", "green": "G", "blue": "B"}


class CurvesPanel(QWidget):
    paramsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._curves: dict[str, list[Point]] = {
            "master": default_curve(),
            "red": default_curve(),
            "green": default_curve(),
            "blue": default_curve(),
        }
        self._active = "master"

        # Channel selector buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        self._buttons: dict[str, QPushButton] = {}
        for key, label in _CHANNEL_NAMES.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._select_channel(k))
            self._buttons[key] = btn
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        self._curve_widget = CurveWidget()
        self._curve_widget.pointsChanged.connect(self._on_curve_changed)
        layout.addWidget(self._curve_widget, 1)
        self._update_buttons()

    def _select_channel(self, channel: str):
        self._active = channel
        self._curve_widget.set_points(self._curves[channel])
        self._update_buttons()

    def _update_buttons(self):
        for key, btn in self._buttons.items():
            btn.setChecked(key == self._active)
            btn.setStyleSheet(
                f"background-color: {'#d4943e' if key == self._active else '#33312e'};"
                f"color: {'#1c1b19' if key == self._active else '#ddd9d4'};"
            )

    def _on_curve_changed(self):
        self._curves[self._active] = self._curve_widget.get_points()
        self.paramsChanged.emit(self.get_params())

    def get_params(self) -> dict:
        return {"curves": {k: v.copy() for k, v in self._curves.items()}}

    def set_curves(self, master=None, red=None, green=None, blue=None):
        if master is not None:
            self._curves["master"] = master
        if red is not None:
            self._curves["red"] = red
        if green is not None:
            self._curves["green"] = green
        if blue is not None:
            self._curves["blue"] = blue
        # Refresh active display
        self._curve_widget.set_points(self._curves[self._active])
        self.update()
