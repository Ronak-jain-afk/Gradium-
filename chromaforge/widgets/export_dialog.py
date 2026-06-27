from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QPushButton, QFileDialog, QLineEdit, QCheckBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal


FORMAT_FILTERS = {
    "JPEG": "(*.jpg)",
    "PNG": "(*.png)",
    "TIFF": "(*.tiff *.tif)",
}


class ExportDialog(QDialog):
    def __init__(self, source_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export")
        self.setMinimumWidth(360)
        self._result_path: str | None = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Source: {source_name}"))

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format:"))
        self._format = QComboBox()
        self._format.addItems(list(FORMAT_FILTERS.keys()))
        self._format.currentTextChanged.connect(self._update_extension)
        fmt_row.addWidget(self._format, 1)
        layout.addLayout(fmt_row)

        qual_row = QHBoxLayout()
        qual_row.addWidget(QLabel("Quality:"))
        self._quality = QSlider(Qt.Orientation.Horizontal)
        self._quality.setRange(10, 100)
        self._quality.setValue(90)
        qual_row.addWidget(self._quality, 1)
        self._qual_label = QLabel("90")
        qual_row.addWidget(self._qual_label)
        self._quality.valueChanged.connect(lambda v: self._qual_label.setText(str(v)))
        layout.addLayout(qual_row)

        self._output_path = QLineEdit()
        self._output_path.setPlaceholderText("Output path...")
        layout.addWidget(self._output_path)

        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        self._export_btn = QPushButton("Export")
        self._export_btn.setDefault(True)
        self._export_btn.clicked.connect(self._do_export)
        btns.addWidget(self._export_btn)
        layout.addLayout(btns)

    def _update_extension(self):
        fmt = self._format.currentText()
        ext_map = {"JPEG": ".jpg", "PNG": ".png", "TIFF": ".tiff"}
        current = self._output_path.text()
        if current:
            p = Path(current)
            self._output_path.setText(str(p.with_suffix(ext_map.get(fmt, ".jpg"))))

    def _browse(self):
        fmt = self._format.currentText()
        filt = FORMAT_FILTERS.get(fmt, "(*.*)")
        path, _ = QFileDialog.getSaveFileName(self, "Save As", str(self._output_path.text()), filt)
        if path:
            self._output_path.setText(path)

    def _do_export(self):
        path = self._output_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Export", "Please choose an output path.")
            return
        self._result_path = path
        self.accept()

    def get_result(self) -> dict:
        return {
            "path": self._result_path,
            "quality": self._quality.value(),
            "format": self._format.currentText(),
        }
