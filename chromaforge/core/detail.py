import numpy as np
import cv2


def apply_sharpen(img: np.ndarray, amount: float = 0.0, radius: float = 1.0) -> np.ndarray:
    if amount == 0:
        return img
    uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    ksize = max(3, int(radius) * 2 + 1)
    blurred = cv2.GaussianBlur(uint8, (ksize, ksize), radius)
    sharpened = cv2.addWeighted(uint8, 1.0 + amount / 50.0, blurred, -amount / 50.0, 0)
    return sharpened.astype(np.float32) / 255.0


def apply_noise_reduction(img: np.ndarray, luminance: float = 0.0, color: float = 0.0) -> np.ndarray:
    if luminance == 0 and color == 0:
        return img
    uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    h = int(luminance * 0.3) or None
    h_color = int(color * 0.3) or None
    template_ws = 7
    search_ws = 21
    result = cv2.fastNlMeansDenoisingColored(
        uint8, None, h or 0, h_color or 0, template_ws, search_ws
    )
    return result.astype(np.float32) / 255.0
