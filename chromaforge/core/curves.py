import numpy as np
import cv2

Point = tuple[float, float]


def default_curve() -> list[Point]:
    return [(0.0, 0.0), (1.0, 1.0)]


def _catmull_rom(p0: Point, p1: Point, p2: Point, p3: Point, t: np.ndarray) -> np.ndarray:
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
    )


def evaluate_curve(points: list[Point], num_samples: int = 256) -> np.ndarray:
    if len(points) < 2:
        return np.linspace(0.0, 1.0, num_samples)
    if len(points) == 2:
        return np.linspace(points[0][1], points[1][1], num_samples)

    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])
    out = np.linspace(0.0, 1.0, num_samples)

    # Extend boundaries for Catmull-Rom
    px = np.concatenate([[2 * xs[0] - xs[1]], xs, [2 * xs[-1] - xs[-2]]])
    py = np.concatenate([[2 * ys[0] - ys[1]], ys, [2 * ys[-1] - ys[-2]]])

    result = np.zeros(num_samples)
    # Set exact endpoint values
    result[0] = ys[0]
    result[-1] = ys[-1]
    idx = np.searchsorted(xs, out, side='left') - 1
    idx = np.clip(idx, 0, len(xs) - 2)

    for i in range(len(xs) - 1):
        mask = idx == i
        if not mask.any():
            continue
        t = (out[mask] - xs[i]) / (xs[i + 1] - xs[i])
        result[mask] = _catmull_rom(
            (px[i], py[i]), (px[i + 1], py[i + 1]),
            (px[i + 2], py[i + 2]), (px[i + 3], py[i + 3]),
            t,
        )

    return np.clip(result, 0.0, 1.0)


def apply_curves(img: np.ndarray, master: list[Point],
                 red: list[Point], green: list[Point], blue: list[Point]) -> np.ndarray:
    uint8 = (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
    lut_m = (evaluate_curve(master) * 255).astype(np.uint8) if master else None
    lut_r = (evaluate_curve(red) * 255).astype(np.uint8) if red else None
    lut_g = (evaluate_curve(green) * 255).astype(np.uint8) if green else None
    lut_b = (evaluate_curve(blue) * 255).astype(np.uint8) if blue else None

    if lut_m is not None:
        uint8 = cv2.LUT(uint8, lut_m)

    channels = list(cv2.split(uint8))
    if lut_r is not None:
        channels[0] = cv2.LUT(channels[0], lut_r)
    if lut_g is not None:
        channels[1] = cv2.LUT(channels[1], lut_g)
    if lut_b is not None:
        channels[2] = cv2.LUT(channels[2], lut_b)

    result = cv2.merge(channels)
    return result.astype(np.float32) / 255.0
