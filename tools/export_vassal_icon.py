"""Build transparent VassalOps knight PNG/ICO from assets/vassal_knight_source.png."""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "storage" / "dashboard"
SOURCE = DASH / "assets" / "vassal_knight_source.png"
OUT_PNG = DASH / "vassal_icon.png"
OUT_ICO = DASH / "vassal_icon.ico"
OUT_MASTER = DASH / "assets" / "vassal_knight.png"

# Splash stage background — used only if a residual fringe remains
SPLASH_BG = (15, 20, 25, 255)  # #0f1419


def remove_background_flood(img: Image.Image, tol: int = 44) -> Image.Image:
    """
    Flood-fill from image edges using the corner seed color.
    Source art uses a murky olive/brown plate (~26,35,30), not pure black —
    so RGB<=28 keying left a visible box. Edge flood removes that plate.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pix = rgba.load()
    sr, sg, sb, _ = pix[0, 0]

    def is_bg(r: int, g: int, b: int) -> bool:
        # Keep bright steel and red accents
        if (r + g + b) / 3.0 > 62:
            return False
        if r >= 90 and r > g + 20 and r > b + 20:
            return False
        return abs(r - sr) <= tol and abs(g - sg) <= tol and abs(b - sb) <= tol

    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    # denser edge seeds so disconnected bg pockets near the border get hit
    for x in range(0, w, 8):
        seeds.append((x, 0))
        seeds.append((x, h - 1))
    for y in range(0, h, 8):
        seeds.append((0, y))
        seeds.append((w - 1, y))

    q: deque = deque()
    seen = set()
    for s in seeds:
        if s not in seen and is_bg(*pix[s[0], s[1]][:3]):
            q.append(s)
            seen.add(s)

    while q:
        x, y = q.popleft()
        r, g, b, _a = pix[x, y]
        if not is_bg(r, g, b):
            continue
        pix[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                nr, ng, nb, _ = pix[nx, ny]
                if is_bg(nr, ng, nb):
                    seen.add((nx, ny))
                    q.append((nx, ny))

    # Second pass: any remaining seed-like dark plate pixels (small islands)
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a == 0:
                continue
            if is_bg(r, g, b):
                # only clear if a neighbor is already transparent (fringe / hole)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and pix[nx, ny][3] == 0:
                        pix[x, y] = (r, g, b, 0)
                        break
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
    cut = remove_background_flood(Image.open(SOURCE))
    cut = trim_alpha(cut, pad=4)
    DASH.mkdir(parents=True, exist_ok=True)
    (DASH / "assets").mkdir(parents=True, exist_ok=True)
    ui = fit_square(cut, 512)
    master = fit_square(cut, 1024)
    ui.save(OUT_PNG, format="PNG")
    master.save(OUT_MASTER, format="PNG")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [fit_square(cut, s[0]) for s in sizes]
    icons[0].save(OUT_ICO, format="ICO", sizes=sizes)
    # sanity: corners must be transparent
    c0 = master.getpixel((0, 0))
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_ICO}")
    print(f"Wrote {OUT_MASTER}")
    print(f"master corner RGBA={c0} (alpha should be 0)")


if __name__ == "__main__":
    main()
