from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt


class CollapsibleSection(QWidget):
    """A collapsible panel section with a clickable header that toggles content visibility."""
    def __init__(self, title: str, content: QWidget, parent=None, collapsed: bool = False):
        super().__init__(parent)
        self._content = content
        self._collapsed = collapsed

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toggle = QPushButton(f" {title}")
        self._toggle.setObjectName("sectionToggle")
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not collapsed)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.clicked.connect(self._toggle_content)
        layout.addWidget(self._toggle)

        self._content.setVisible(not collapsed)
        layout.addWidget(self._content)

    def _toggle_content(self, checked: bool):
        self._content.setVisible(checked)
        self._toggle.setChecked(checked)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._toggle.setChecked(not collapsed)
        self._content.setVisible(not collapsed)
