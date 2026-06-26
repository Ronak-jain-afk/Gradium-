import numpy as np
import cv2

# Band centers (0-360 hue range) and half-widths for smooth masks
BANDS = {
    "red":     {"center": 0,   "half": 30},
    "orange":  {"center": 30,  "half": 20},
    "yellow":  {"center": 55,  "half": 25},
    "green":   {"center": 110, "half": 45},
    "aqua":    {"center": 170, "half": 30},
    "blue":    {"center": 225, "half": 40},
    "purple":  {"center": 280, "half": 30},
    "magenta": {"center": 320, "half": 30},
}


def _hue_weight(hue: np.ndarray, center: float, half: float) -> np.ndarray:
    """Smooth cosine weight for a hue band. hue is 0-360."""
    diff = np.abs(hue - center)
    diff = np.minimum(diff, 360.0 - diff)
    # Cosine falloff: weight=1 at center, ~0 at half-width boundary
    return np.clip(np.cos(diff / half * np.pi * 0.5), 0.0, 1.0)


def apply_hsl(img: np.ndarray, **bands: dict) -> np.ndarray:
    """Apply per-band HSL adjustments.

    params: {"red": {"hue": 0, "saturation": 0, "luminance": 0}, ...}
    Each value is ±100 scale.
    """
    has_work = any(
        v.get("hue", 0) or v.get("saturation", 0) or v.get("luminance", 0)
        for v in bands.values()
    )
    if not has_work:
        return img

    uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    hsv = cv2.cvtColor(uint8, cv2.COLOR_RGB2HSV).astype(np.float32)
    h = hsv[:, :, 0] * 2.0     # 0-358 → 0-360
    s = hsv[:, :, 1]           # 0-255
    v = hsv[:, :, 2]           # 0-255

    total_weight = np.zeros_like(h)
    hue_shift = np.zeros_like(h)
    sat_scale = np.ones_like(h)
    lum_shift = np.zeros_like(h)

    for band_name, adj in bands.items():
        band = BANDS.get(band_name)
        if band is None:
            continue
        h_adj = adj.get("hue", 0)
        s_adj = adj.get("saturation", 0)
        l_adj = adj.get("luminance", 0)

        if h_adj == 0 and s_adj == 0 and l_adj == 0:
            continue

        weight = _hue_weight(h, band["center"], band["half"])
        total_weight += weight

        if h_adj:
            hue_shift += weight * (h_adj / 100.0 * band["half"])
        if s_adj:
            sat_scale += weight * (s_adj / 100.0)
        if l_adj:
            lum_shift += weight * (l_adj / 100.0 * 255.0)

    # Normalize by total weight where multiple bands overlap
    overlap = total_weight > 1.0
    if overlap.any():
        hue_shift[overlap] /= total_weight[overlap]
        sat_scale[overlap] = 1.0 + (sat_scale[overlap] - 1.0) / total_weight[overlap]
        lum_shift[overlap] /= total_weight[overlap]

    h = (h + hue_shift) % 360.0
    s = np.clip(s * sat_scale, 0.0, 255.0)
    v = np.clip(v + lum_shift, 0.0, 255.0)

    hsv[:, :, 0] = h / 2.0   # Back to OpenCV range (0-180)
    hsv[:, :, 1] = s
    hsv[:, :, 2] = v

    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return result.astype(np.float32) / 255.0
