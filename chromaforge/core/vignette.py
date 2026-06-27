import numpy as np
import cv2


def apply_vignette(img: np.ndarray, amount: float = 0.0, midpoint: float = 50.0,
                   roundness: float = 0.0, feather: float = 50.0) -> np.ndarray:
    if amount == 0:
        return img

    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    max_dim = max(w, h) / 2.0
    mid = midpoint / 100.0
    fth = feather / 100.0

    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - center[0]) / max_dim
    dy = (yy - center[1]) / max_dim

    # Roundness control: squash the y-axis
    r_factor = 1.0 + roundness / 100.0
    dy = dy / max(r_factor, 0.01)

    dist = np.sqrt(dx * dx + dy * dy)

    # Parametric vignette: smooth falloff from midpoint
    falloff = np.clip((dist - mid) / max(fth, 0.01), 0.0, 1.0)
    mask = 1.0 - falloff * falloff * (3.0 - 2.0 * falloff)  # smoothstep

    # amount > 0 = darken, amount < 0 = brighten
    strength = abs(amount) / 100.0
    if amount > 0:
        # Darken edges
        darken = 1.0 - mask * strength
        return np.clip(img * darken[..., np.newaxis], 0.0, 1.0)
    else:
        # Brighten edges
        brighten = 1.0 + (1.0 - mask) * strength
        return np.clip(img * brighten[..., np.newaxis], 0.0, 1.0)
