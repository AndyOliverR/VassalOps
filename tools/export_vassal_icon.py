"""Build transparent VassalOps knight PNG/ICO from assets/vassal_knight_source.png."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "storage" / "dashboard"
SOURCE = DASH / "assets" / "vassal_knight_source.png"
OUT_PNG = DASH / "vassal_icon.png"
OUT_ICO = DASH / "vassal_icon.ico"
OUT_MASTER = DASH / "assets" / "vassal_knight.png"


def key_black_to_alpha(img: Image.Image, threshold: int = 28) -> Image.Image:
    """Make near-black background transparent; keep silver/steel/red figure."""
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def trim_alpha(img: Image.Image, pad: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.width, right + pad)
    bottom = min(img.height, bottom + pad)
    return img.crop((left, top, right, bottom))


def fit_square(img: Image.Image, size: int) -> Image.Image:
    """Contain knight in a transparent square canvas."""
    scaled = img.copy()
    scaled.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - scaled.width) // 2
    oy = (size - scaled.height) // 2
    canvas.paste(scaled, (ox, oy), scaled)
    return canvas


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing source: {SOURCE}")
    cut = key_black_to_alpha(Image.open(SOURCE))
    cut = trim_alpha(cut, pad=6)
    DASH.mkdir(parents=True, exist_ok=True)
    (DASH / "assets").mkdir(parents=True, exist_ok=True)
    fit_square(cut, 512).save(OUT_PNG, format="PNG")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [fit_square(cut, s[0]) for s in sizes]
    icons[0].save(OUT_ICO, format="ICO", sizes=sizes)
    fit_square(cut, 1024).save(OUT_MASTER, format="PNG")
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_ICO}")
    print(f"Wrote {OUT_MASTER}")


if __name__ == "__main__":
    main()
