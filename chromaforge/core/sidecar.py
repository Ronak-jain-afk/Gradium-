from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
from typing import Any, Optional, get_type_hints


@dataclass
class WhiteBalanceParams:
    temperature: float = 0.0
    tint: float = 0.0


@dataclass
class TonalParams:
    exposure: float = 0.0
    contrast: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    whites: float = 0.0
    blacks: float = 0.0
    brightness: float = 0.0


@dataclass
class ColorParams:
    saturation: float = 0.0
    vibrance: float = 0.0
    hue: float = 0.0


@dataclass
class HSLBand:
    hue: float = 0.0
    saturation: float = 0.0
    luminance: float = 0.0


@dataclass
class HSLParams:
    red: HSLBand = field(default_factory=HSLBand)
    orange: HSLBand = field(default_factory=HSLBand)
    yellow: HSLBand = field(default_factory=HSLBand)
    green: HSLBand = field(default_factory=HSLBand)
    aqua: HSLBand = field(default_factory=HSLBand)
    blue: HSLBand = field(default_factory=HSLBand)
    purple: HSLBand = field(default_factory=HSLBand)
    magenta: HSLBand = field(default_factory=HSLBand)


@dataclass
class SplitToningParams:
    shadowHue: float = 0.0
    shadowSat: float = 0.0
    highlightHue: float = 0.0
    highlightSat: float = 0.0
    balance: float = 0.0


@dataclass
class CurvesParams:
    master: list[tuple[float, float]] = field(default_factory=list)
    red: list[tuple[float, float]] = field(default_factory=list)
    green: list[tuple[float, float]] = field(default_factory=list)
    blue: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class DetailParams:
    sharpenAmount: float = 0.0
    sharpenRadius: float = 0.0
    noiseLuminance: float = 0.0
    noiseColor: float = 0.0


@dataclass
class VignetteParams:
    amount: float = 0.0
    midpoint: float = 50.0
    roundness: float = 0.0
    feather: float = 50.0


@dataclass
class GeometryParams:
    crop: list[float] | None = None
    rotationDegrees: float = 0.0
    flipH: bool = False
    flipV: bool = False


@dataclass
class EditParams:
    whiteBalance: WhiteBalanceParams = field(default_factory=WhiteBalanceParams)
    tonal: TonalParams = field(default_factory=TonalParams)
    color: ColorParams = field(default_factory=ColorParams)
    hsl: HSLParams = field(default_factory=HSLParams)
    splitToning: SplitToningParams = field(default_factory=SplitToningParams)
    curves: CurvesParams = field(default_factory=CurvesParams)
    detail: DetailParams = field(default_factory=DetailParams)
    vignette: VignetteParams = field(default_factory=VignetteParams)
    geometry: GeometryParams = field(default_factory=GeometryParams)


@dataclass
class Sidecar:
    schemaVersion: int = 1
    sourceFile: str = ""
    edits: EditParams = field(default_factory=EditParams)
    history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Sidecar':
        return _from_dict(cls, data)


def _from_dict(cls: type, data: dict) -> Any:
    """Recursive dataclass reconstruction from dict, ignoring unknown keys."""
    if not hasattr(cls, '__dataclass_fields__'):
        return data

    hints = get_type_hints(cls)
    kwargs = {}
    for name in cls.__dataclass_fields__:
        if name not in data:
            continue
        field_type = hints.get(name, type(data[name]))
        origin = getattr(field_type, '__origin__', None)
        if origin is list:
            kwargs[name] = data[name]
        elif isinstance(field_type, type) and hasattr(field_type, '__dataclass_fields__'):
            kwargs[name] = _from_dict(field_type, data[name])
        else:
            kwargs[name] = data[name]
    return cls(**kwargs)


def sidecar_path(image_path: Path) -> Path:
    return image_path.with_suffix(image_path.suffix + ".chromaforge.json")


def load_sidecar(image_path: Path) -> Optional[Sidecar]:
    sp = sidecar_path(image_path)
    if not sp.exists():
        return None
    try:
        with open(sp) as f:
            data = json.load(f)
        return Sidecar.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_sidecar(image_path: Path, sidecar: Sidecar) -> None:
    sp = sidecar_path(image_path)
    with open(sp, "w") as f:
        json.dump(sidecar.to_dict(), f, indent=2)
