import numpy as np
import cv2
from pathlib import Path
from PySide6.QtGui import QImage
from .constants import PREVIEW_LONG_EDGE

_RAW_EXTENSIONS = frozenset({
    ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".dng", ".raf", ".orf",
    ".rw2", ".pef", ".srw", ".x3f", ".raw", ".rwl", ".sr2", ".srf",
    ".3fr", ".ari", ".bay", ".bmq", ".cap", ".cine", ".cs1", ".dcr",
    ".drf", ".dsc", ".erf", ".fff", ".iiq", ".k25", ".kdc", ".mdc",
    ".mef", ".mos", ".mrw", ".stn",
})


def load_image(path: str | Path) -> np.ndarray | None:
    path = Path(path)
    if not path.exists():
        return None
    if path.suffix.lower() in _RAW_EXTENSIONS:
        return load_raw(path)
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return None
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img_rgb.astype(np.float32) / 255.0


def load_raw(path: Path) -> np.ndarray | None:
    try:
        import rawpy
        raw = rawpy.imread(str(path))
        rgb = raw.postprocess(use_camera_wb=True, output_bps=16, no_auto_bright=True, user_flip=0)
        raw.close()
        return rgb.astype(np.float32) / 65535.0
    except Exception:
        return None


def compute_downsampled(img: np.ndarray, long_edge: int = PREVIEW_LONG_EDGE) -> np.ndarray:
    h, w = img.shape[:2]
    current_long = max(h, w)
    if current_long <= long_edge:
        return img
    scale = long_edge / current_long
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA).astype(np.float32)


def array_to_qimage(img: np.ndarray) -> QImage:
    h, w = img.shape[:2]
    uint8_img = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    if uint8_img.shape[2] == 3:
        return QImage(uint8_img.data, w, h, w * 3, QImage.Format.Format_RGB888).copy()
    if uint8_img.shape[2] == 4:
        return QImage(uint8_img.data, w, h, w * 4, QImage.Format.Format_RGBA8888).copy()
    raise ValueError(f"Unexpected image channels: {uint8_img.shape[2]}")
