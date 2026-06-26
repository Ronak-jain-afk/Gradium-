import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, QThread
from .pipeline import ProcessingPipeline


class PipelineWorker(QObject):
    finished = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pipeline = ProcessingPipeline()
        self._input: np.ndarray | None = None

    def set_input(self, img: np.ndarray):
        self._input = img

    def set_params(self, params: dict[str, dict]):
        self._pipeline.set_params(params)

    @Slot()
    def process(self):
        if self._input is None:
            return
        result = self._pipeline.apply(self._input)
        self.finished.emit(result)


class PipelineThread(QObject):
    """Owns a QThread and PipelineWorker. Simple signal-based API."""
    resultReady = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = QThread(self)
        self._worker = PipelineWorker()
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self.resultReady)
        self._thread.start()

    def set_input(self, img: np.ndarray):
        self._worker.set_input(img)

    def set_params(self, params: dict[str, dict]):
        self._worker.set_params(params)

    def request_process(self):
        self._worker.process()

    def stop(self):
        self._thread.quit()
        self._thread.wait()
