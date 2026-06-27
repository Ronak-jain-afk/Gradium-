from typing import Callable
import numpy as np
import cv2
from . import constants
from .hsl import apply_hsl
from .split_toning import apply_split_toning
from .curves import apply_curves
from .detail import apply_sharpen, apply_noise_reduction
from .vignette import apply_vignette
from .crop import apply_crop_rotate


def apply_exposure(img: np.ndarray, stops: float) -> np.ndarray:
    factor = 2.0 ** stops
    return np.clip(img * factor, 0.0, 1.0)


def apply_contrast(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    factor = (100.0 + amount) / 100.0 if amount > 0 else 100.0 / (100.0 - amount)
    midpoint = 0.5
    return np.clip(((img - midpoint) * factor) + midpoint, 0.0, 1.0)


def _smooth_weight(x: np.ndarray, pivot: float = 0.5, steepness: float = 4.0) -> np.ndarray:
    """Smoothstep-like weighting for highlights/shadows separation."""
    return 1.0 / (1.0 + np.exp(-steepness * (x - pivot)))


def apply_highlights(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    weight = _smooth_weight(img, 0.5, 5.0)
    factor = (100.0 + amount) / 100.0 if amount > 0 else 100.0 / (100.0 - amount)
    return np.clip(((img - 0.5) * weight * (factor - 1.0) + img), 0.0, 1.0)


def apply_shadows(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    weight = 1.0 - _smooth_weight(img, 0.5, 5.0)
    factor = (100.0 + amount) / 100.0 if amount > 0 else 100.0 / (100.0 - amount)
    return np.clip(((img - 0.5) * weight * (factor - 1.0) + img), 0.0, 1.0)


def apply_whites(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    weight = _smooth_weight(img, 0.75, 8.0)
    delta = weight * (amount / 100.0) * 0.25
    return np.clip(img + delta * (1.0 - img), 0.0, 1.0)


def apply_blacks(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    weight = 1.0 - _smooth_weight(img, 0.25, 8.0)
    delta = weight * (amount / 100.0) * 0.25
    return np.clip(img - delta * img, 0.0, 1.0)


def apply_brightness(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    factor = 1.0 + amount / 200.0
    return np.clip(img ** (1.0 / max(factor, 0.01)), 0.0, 1.0)


def apply_saturation(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * ((100.0 + amount) / 100.0), 0.0, 255.0)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0


def apply_vibrance(img: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return img
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    s = hsv[:, :, 1] / 255.0
    boost = amount / 100.0
    # Boost less-saturated pixels more, protect already-saturated ones
    weight = 1.0 - s
    hsv[:, :, 1] = np.clip((s + weight * boost) * 255.0, 0.0, 255.0)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0


def apply_white_balance(img: np.ndarray, temperature: float = 0.0, tint: float = 0.0) -> np.ndarray:
    if temperature == 0 and tint == 0:
        return img
    result = img.copy().astype(np.float32)
    t_shift = temperature / 100.0 * 0.1
    tn_shift = tint / 100.0 * 0.1
    result[:, :, 0] = np.clip(result[:, :, 0] + t_shift, 0.0, 1.0)
    result[:, :, 2] = np.clip(result[:, :, 2] - t_shift, 0.0, 1.0)
    result[:, :, 1] = np.clip(result[:, :, 1] + tn_shift, 0.0, 1.0)
    return result


def apply_hue(img: np.ndarray, degrees: float) -> np.ndarray:
    if degrees == 0:
        return img
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 0] = (hsv[:, :, 0] + degrees) % 360.0
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0


_PIPELINE_STEPS: dict[str, Callable] = {
    "whiteBalance": apply_white_balance,
    "exposure": apply_exposure,
    "contrast": apply_contrast,
    "highlights": apply_highlights,
    "shadows": apply_shadows,
    "whites": apply_whites,
    "blacks": apply_blacks,
    "brightness": apply_brightness,
    "hsl": apply_hsl,
    "saturation": apply_saturation,
    "splitToning": apply_split_toning,
    "curves": apply_curves,
    "sharpening": apply_sharpen,
    "noiseReduction": apply_noise_reduction,
    "vibrance": apply_vibrance,
    "hue": apply_hue,
    "vignette": apply_vignette,
    "cropRotate": apply_crop_rotate,
}


class ProcessingPipeline:
    def __init__(self):
        self.steps: list[tuple[str, Callable, dict]] = []

    def set_params(self, params: dict[str, dict]):
        self.steps.clear()
        for step_name in constants.PIPELINE_ORDER:
            if step_name in params and step_name in _PIPELINE_STEPS:
                fn = _PIPELINE_STEPS[step_name]
                self.steps.append((step_name, fn, params[step_name]))

    def apply(self, img: np.ndarray) -> np.ndarray:
        result = img.copy()
        for _name, fn, step_params in self.steps:
            result = fn(result, **step_params)
        return result
