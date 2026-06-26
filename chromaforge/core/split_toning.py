import numpy as np
import cv2


def _smoothstep(x: np.ndarray, edge0: float = 0.0, edge1: float = 1.0) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def apply_split_toning(img: np.ndarray,
                      shadowHue: float = 0.0, shadowSat: float = 0.0,
                      highlightHue: float = 0.0, highlightSat: float = 0.0,
                      balance: float = 0.0) -> np.ndarray:
    if shadowSat == 0 and highlightSat == 0:
        return img

    uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    hsv = cv2.cvtColor(uint8, cv2.COLOR_RGB2HSV).astype(np.float32)
    lum = hsv[:, :, 2] / 255.0

    balance_point = 0.5 + balance / 200.0
    hl_weight = _smoothstep(lum, balance_point - 0.2, balance_point + 0.2)

    result = img.astype(np.float32).copy()

    if shadowSat > 0:
        sh_hsv = np.zeros_like(hsv)
        sh_hsv[:, :, 0] = shadowHue / 2.0
        sh_hsv[:, :, 1] = shadowSat / 100.0 * 255.0
        sh_hsv[:, :, 2] = 255.0
        sh_rgb = cv2.cvtColor(sh_hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0
        sh_weight = (1.0 - hl_weight) * (shadowSat / 100.0)
        result = result * (1.0 - sh_weight[..., np.newaxis]) + sh_rgb * sh_weight[..., np.newaxis]

    if highlightSat > 0:
        hl_hsv = np.zeros_like(hsv)
        hl_hsv[:, :, 0] = highlightHue / 2.0
        hl_hsv[:, :, 1] = highlightSat / 100.0 * 255.0
        hl_hsv[:, :, 2] = 255.0
        hl_rgb = cv2.cvtColor(hl_hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0
        hl_weight = hl_weight * (highlightSat / 100.0)
        result = result * (1.0 - hl_weight[..., np.newaxis]) + hl_rgb * hl_weight[..., np.newaxis]

    return np.clip(result, 0.0, 1.0)
