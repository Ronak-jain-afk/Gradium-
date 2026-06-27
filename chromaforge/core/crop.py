import numpy as np
import cv2


def apply_crop_rotate(img: np.ndarray, crop: list[float] | None = None,
                      rotationDegrees: float = 0.0,
                      flipH: bool = False, flipV: bool = False) -> np.ndarray:
    result = img.copy()
    h, w = result.shape[:2]

    if crop is not None and len(crop) == 4:
        l, t, r, b = crop
        l = max(0.0, min(float(l), 1.0))
        t = max(0.0, min(float(t), 1.0))
        r = max(0.0, min(float(r), 1.0))
        b = max(0.0, min(float(b), 1.0))
        if l < r and t < b:
            x1, y1 = int(l * w), int(t * h)
            x2, y2 = int(r * w), int(b * h)
            result = result[y1:y2, x1:x2]

    h, w = result.shape[:2]

    if rotationDegrees != 0.0:
        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, rotationDegrees, 1.0)
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        M[0, 2] += new_w / 2.0 - center[0]
        M[1, 2] += new_h / 2.0 - center[1]
        result = cv2.warpAffine(result, M, (new_w, new_h),
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    if flipH and flipV:
        result = cv2.flip(result, -1)
    elif flipH:
        result = cv2.flip(result, 1)
    elif flipV:
        result = cv2.flip(result, 0)

    return result
