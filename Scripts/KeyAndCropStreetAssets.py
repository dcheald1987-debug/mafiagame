"""Key grey studio backgrounds on new street crowd / prop / car JPGs → PNG alpha."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CROP = ROOT / "Content" / "Art" / "Empire" / "Sprites" / "Source" / "Cropped"

FILES = [
    CROP / "Characters" / "S_RivalThug.jpg",
    CROP / "Characters" / "S_Cop.jpg",
    CROP / "Characters" / "S_Bartender.jpg",
    CROP / "Characters" / "S_CivWoman_B.jpg",
    CROP / "Characters" / "S_Newsboy.jpg",
    CROP / "Cars" / "S_ModelA.jpg",
    CROP / "Cars" / "S_PoliceCar.jpg",
    CROP / "Cars" / "S_Taxi.jpg",
    CROP / "Cars" / "S_DeliveryTruck.jpg",
    CROP / "Props" / "S_LampHead.jpg",
    CROP / "Props" / "S_LampHead_Broken.jpg",
    CROP / "Props" / "S_TrafficHead.jpg",
    CROP / "Props" / "S_TrafficHead_Side.jpg",
    CROP / "Props" / "S_TrafficPole.jpg",
    CROP / "Props" / "S_PedSignal.jpg",
]


def key_grey(im: Image.Image, thresh: float = 32.0, grey_lo: int = 70, grey_hi: int = 210) -> Image.Image:
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, _a = px[x, y]
            mx = max(r, g, b)
            mn = min(r, g, b)
            if (mx - mn) < thresh and grey_lo <= (r + g + b) // 3 <= grey_hi:
                px[x, y] = (r, g, b, 0)
            else:
                px[x, y] = (r, g, b, 255)
    return rgba


def bbox_opaque(im: Image.Image, pad: int = 6):
    box = im.split()[-1].getbbox()
    if not box:
        return (0, 0, im.width, im.height)
    l, t, r, b = box
    return (
        max(0, l - pad),
        max(0, t - pad),
        min(im.width, r + pad),
        min(im.height, b + pad),
    )


def process(path: Path) -> None:
    if not path.is_file():
        print("missing", path)
        return
    im = key_grey(Image.open(path))
    im = im.crop(bbox_opaque(im))
    out = path.with_suffix(".png")
    im.save(out, "PNG")
    print("wrote", out.name, im.size)


def main():
    for f in FILES:
        process(f)


if __name__ == "__main__":
    main()
