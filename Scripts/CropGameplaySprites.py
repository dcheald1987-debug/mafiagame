"""
Crop concept sheets into single gameplay sprites (PNG with alpha).
Keys out near-grey studio backgrounds. Writes Content/.../Sprites/Source/Cropped/
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Content" / "Art" / "Empire" / "Sprites" / "Source"
OUT = SRC / "Cropped"


def key_grey(im: Image.Image, thresh: float = 28.0, grey_lo: int = 90, grey_hi: int = 200) -> Image.Image:
    """Make near-uniform grey studio BG transparent; keep subject opaque."""
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            mx = max(r, g, b)
            mn = min(r, g, b)
            # low chroma + mid luminance ≈ studio grey
            if (mx - mn) < thresh and grey_lo <= (r + g + b) // 3 <= grey_hi:
                px[x, y] = (r, g, b, 0)
            else:
                px[x, y] = (r, g, b, 255)
    return rgba


def bbox_opaque(im: Image.Image, pad: int = 4) -> tuple[int, int, int, int]:
    alpha = im.split()[-1]
    box = alpha.getbbox()
    if not box:
        return (0, 0, im.width, im.height)
    l, t, r, b = box
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    return (l, t, r, b)


def key_black(im: Image.Image, thresh: int = 18) -> Image.Image:
    """Knock out near-black studio backdrops left after grey key."""
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r <= thresh and g <= thresh and b <= thresh:
                px[x, y] = (r, g, b, 0)
    return rgba


def crop_char_front(path: Path, out_name: str) -> Path:
    """4-view horizontal turnaround → leftmost (front) panel, keyed + trimmed."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # Harlan crew is 3 figures side by side — take left figure
    name = path.stem
    if "HarlanCrew" in name:
        panel = im.crop((0, 0, w // 3, h))
    else:
        panel = im.crop((0, 0, w // 4, h))
    keyed = key_black(key_grey(panel))
    keyed = keyed.crop(bbox_opaque(keyed))
    dest = OUT / "Characters" / out_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    keyed.save(dest, "PNG")
    return dest


def crop_building_hero(path: Path, out_name: str) -> Path:
    """Single elevation: left panel of dual-view sheets; street row stays full width."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    name = path.stem
    if "StreetRow" in name:
        region = im
    elif "Bar" in name or "Hawser" in name:
        region = im.crop((0, 0, int(w * 0.48), int(h * 0.55)))
    else:
        # dual front+side sheets → left elevation only
        region = im.crop((0, 0, int(w * 0.48), h))
    keyed = key_grey(region, thresh=32.0, grey_lo=70, grey_hi=210)
    keyed = key_black(keyed)
    keyed = keyed.crop(bbox_opaque(keyed, pad=6))
    dest = OUT / "Buildings" / out_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    keyed.save(dest, "PNG")
    return dest


def crop_car_three_q(path: Path, out_name: str) -> Path:
    """2x2 car sheet → bottom-right or largest 3/4 cell."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # try bottom-right quadrant first (often 3/4 hero)
    cells = [
        im.crop((w // 2, h // 2, w, h)),
        im.crop((0, h // 2, w // 2, h)),
        im.crop((w // 2, 0, w, h // 2)),
        im.crop((0, 0, w // 2, h // 2)),
    ]
    best = None
    best_area = 0
    for cell in cells:
        keyed = key_black(key_grey(cell))
        box = keyed.split()[-1].getbbox()
        if not box:
            continue
        area = (box[2] - box[0]) * (box[3] - box[1])
        if area > best_area:
            best_area = area
            best = keyed.crop(bbox_opaque(keyed))
    if best is None:
        keyed = key_black(key_grey(im))
        best = keyed.crop(bbox_opaque(keyed))
    dest = OUT / "Cars" / out_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    best.save(dest, "PNG")
    return dest


JOBS = [
    ("Characters/T_Char_Eddie.jpg", "char", "S_Eddie.png"),
    ("Characters/T_Char_Nicky.jpg", "char", "S_Nicky.png"),
    ("Characters/T_Char_Nora.jpg", "char", "S_Nora.png"),
    ("Characters/T_Char_HarlanCrew.jpg", "char", "S_Harlan.png"),
    ("Characters/T_Char_DockWorker.jpg", "char", "S_DockWorker.png"),
    ("Characters/T_Char_CivMan.jpg", "char", "S_CivMan.png"),
    ("Characters/T_Char_CivWoman.jpg", "char", "S_CivWoman.png"),
    ("Buildings/T_Bld_Garage.jpg", "bld", "S_Garage.png"),
    ("Buildings/T_Bld_Cafe.jpg", "bld", "S_Cafe.png"),
    ("Buildings/T_Bld_Dock.jpg", "bld", "S_Dock.png"),
    ("Buildings/T_Bld_Bar.jpg", "bld", "S_Bar.png"),
    ("Buildings/T_Bld_Board.jpg", "bld", "S_Board.png"),
    ("Buildings/T_Bld_Freight.jpg", "bld", "S_Freight.png"),
    ("Buildings/T_Bld_Rope.jpg", "bld", "S_Rope.png"),
    ("Buildings/T_Bld_StreetRow.jpg", "bld", "S_StreetRow.png"),
    ("Cars/T_Car_Packard.jpg", "car", "S_Packard.png"),
    ("Cars/T_Car_Harlan.jpg", "car", "S_HarlanSedan.png"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for rel, kind, out_name in JOBS:
        src = SRC / rel.replace("/", os.sep)
        if not src.is_file():
            print("MISSING", src)
            continue
        if kind == "char":
            dest = crop_char_front(src, out_name)
        elif kind == "bld":
            dest = crop_building_hero(src, out_name)
        else:
            dest = crop_car_three_q(src, out_name)
        print("OK", dest.relative_to(ROOT), dest.stat().st_size)
        written.append(str(dest))
    print("CROPPED", len(written))


if __name__ == "__main__":
    main()
