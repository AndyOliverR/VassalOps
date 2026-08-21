"""Rasterize the original VassalOps mark to PNG + ICO (Pillow). Run from repo root."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "storage" / "dashboard"
TEAL = (49, 151, 149, 255)
TEAL_DARK = (35, 78, 82, 255)
NAVY = (26, 32, 44, 255)
SLATE = (45, 55, 72, 255)
MINT = (129, 230, 217, 255)
CREAM = (226, 232, 240, 255)
TUNIC = (44, 122, 123, 255)


def draw_mark(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 128.0

    def xy(x: float, y: float):
        return (x * s, y * s)

    def r(v: float) -> float:
        return v * s

    # Badge
    d.ellipse([xy(4, 4), xy(124, 124)], fill=NAVY)
    d.ellipse([xy(10, 10), xy(118, 118)], fill=TEAL_DARK, outline=TEAL, width=max(2, int(4 * s)))

    cx, cy = 64 * s, 72 * s

    # Legs
    for dx in (-7, 7):
        lx = cx + dx * s
        d.rounded_rectangle(
            [lx - 4 * s, cy + 26 * s, lx + 4 * s, cy + 46 * s],
            radius=max(1, int(3 * s)),
            fill=SLATE,
        )
        d.rounded_rectangle(
            [lx - 5 * s, cy + 42 * s, lx + 5 * s, cy + 47 * s],
            radius=max(1, int(2 * s)),
            fill=NAVY,
        )

    # Arms
    # left
    d.rounded_rectangle(
        [cx - 26 * s, cy - 8 * s, cx - 10 * s, cy + 14 * s],
        radius=max(1, int(3 * s)),
        fill=MINT,
    )
    # right + shield
    d.rounded_rectangle(
        [cx + 10 * s, cy - 8 * s, cx + 26 * s, cy + 14 * s],
        radius=max(1, int(3 * s)),
        fill=MINT,
    )
    sh_c = (cx + 22 * s, cy + 8 * s)
    sh_r = 10 * s
    d.ellipse(
        [sh_c[0] - sh_r, sh_c[1] - sh_r, sh_c[0] + sh_r, sh_c[1] + sh_r],
        fill=TEAL,
        outline=CREAM,
        width=max(1, int(2 * s)),
    )
    d.line([sh_c[0], sh_c[1] - 6 * s, sh_c[0], sh_c[1] + 6 * s], fill=CREAM, width=max(1, int(1.5 * s)))
    d.line([sh_c[0] - 5 * s, sh_c[1], sh_c[0] + 5 * s, sh_c[1]], fill=CREAM, width=max(1, int(1.5 * s)))

    # Torso
    d.polygon(
        [
            (cx - 14 * s, cy - 8 * s),
            (cx + 14 * s, cy - 8 * s),
            (cx + 12 * s, cy + 22 * s),
            (cx - 12 * s, cy + 22 * s),
        ],
        fill=TUNIC,
    )
    d.rounded_rectangle(
        [cx - 10 * s, cy - 12 * s, cx + 10 * s, cy - 2 * s],
        radius=max(1, int(2 * s)),
        fill=TEAL,
    )

    # Helmet
    hx, hy = cx, cy - 24 * s
    d.ellipse([hx - 12 * s, hy - 11 * s, hx + 12 * s, hy + 11 * s], fill=(74, 85, 104, 255))
    d.rectangle([hx - 12 * s, hy - 2 * s, hx + 12 * s, hy + 4 * s], fill=NAVY)
    d.rounded_rectangle(
        [hx - 4 * s, hy - 14 * s, hx + 4 * s, hy - 8 * s],
        radius=max(1, int(1 * s)),
        fill=MINT,
    )

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = draw_mark(256)
    png_path = OUT_DIR / "vassal_icon.png"
    ico_path = OUT_DIR / "vassal_icon.ico"
    base.save(png_path, format="PNG")
    # Multi-size ICO for Windows shortcuts
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [base.resize(sz, Image.Resampling.LANCZOS) for sz in sizes]
    icons[0].save(ico_path, format="ICO", sizes=sizes)
    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
