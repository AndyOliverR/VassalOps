"""Rasterize the original VassalOps mark to high-res PNG + ICO (Pillow). Run from repo root."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "storage" / "dashboard"
TEAL = (49, 151, 149, 255)
TEAL_DARK = (35, 78, 82, 255)
TEAL_MID = (44, 122, 123, 255)
NAVY = (26, 32, 44, 255)
SLATE = (45, 55, 72, 255)
MINT = (129, 230, 217, 255)
CREAM = (226, 232, 240, 255)
HELMET = (74, 85, 104, 255)


def draw_mark(size: int = 1024) -> Image.Image:
    """Draw the same geometry as vassal_mark.svg (viewBox 0..256)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 256.0

    def xy(x: float, y: float):
        return (x * s, y * s)

    def w(v: float) -> int:
        return max(1, int(round(v * s)))

    # Badge rings
    d.ellipse([xy(4, 4), xy(252, 252)], fill=NAVY)
    d.ellipse([xy(16, 16), xy(240, 240)], fill=TEAL_DARK, outline=TEAL, width=w(6))
    d.ellipse([xy(24, 24), xy(232, 232)], outline=TEAL_MID, width=w(1.25))

    cx, cy = 128 * s, 148 * s

    # Legs
    for dx in (-14, 14):
        lx = cx + dx * s
        d.rounded_rectangle(
            [lx - 6 * s, cy + 52 * s, lx + 6 * s, cy + 92 * s],
            radius=max(1, w(4)),
            fill=SLATE,
        )
        d.rounded_rectangle(
            [lx - 8 * s, cy + 86 * s, lx + 8 * s, cy + 95 * s],
            radius=max(1, w(2.5)),
            fill=NAVY,
        )

    # Left arm
    d.rounded_rectangle(
        [cx - 52 * s, cy - 14 * s, cx - 22 * s, cy + 30 * s],
        radius=max(1, w(4)),
        fill=MINT,
    )
    # Right arm
    d.rounded_rectangle(
        [cx + 22 * s, cy - 14 * s, cx + 52 * s, cy + 26 * s],
        radius=max(1, w(4)),
        fill=MINT,
    )
    # Shield
    sh = (cx + 48 * s, cy + 14 * s)
    sr = 18 * s
    d.ellipse([sh[0] - sr, sh[1] - sr, sh[0] + sr, sh[1] + sr], fill=TEAL, outline=CREAM, width=w(2.5))
    d.line([sh[0], sh[1] - 14 * s, sh[0], sh[1] + 14 * s], fill=CREAM, width=w(2))
    d.line([sh[0] - 8 * s, sh[1], sh[0] + 8 * s, sh[1]], fill=CREAM, width=w(2))

    # Torso
    d.polygon(
        [
            (cx - 28 * s, cy - 12 * s),
            (cx + 28 * s, cy - 12 * s),
            (cx + 24 * s, cy + 48 * s),
            (cx - 24 * s, cy + 48 * s),
        ],
        fill=TEAL_MID,
    )
    d.polygon(
        [
            (cx - 28 * s, cy - 12 * s),
            (cx + 28 * s, cy - 12 * s),
            (cx + 26 * s, cy - 2 * s),
            (cx - 26 * s, cy - 2 * s),
        ],
        fill=TEAL,
    )
    d.rounded_rectangle(
        [cx - 20 * s, cy - 24 * s, cx + 20 * s, cy - 6 * s],
        radius=max(1, w(3)),
        fill=TEAL,
        outline=MINT,
        width=w(1),
    )

    # Helmet
    hx, hy = cx, cy - 46 * s
    d.ellipse([hx - 24 * s, hy - 20 * s, hx + 24 * s, hy + 24 * s], fill=HELMET)
    d.rounded_rectangle(
        [hx - 22 * s, hy - 4 * s, hx + 22 * s, hy + 5 * s],
        radius=max(1, w(1.5)),
        fill=NAVY,
    )
    d.rounded_rectangle(
        [hx - 7 * s, hy - 28 * s, hx + 7 * s, hy - 16 * s],
        radius=max(1, w(2)),
        fill=MINT,
    )
    d.rounded_rectangle(
        [hx - 7 * s, hy - 28 * s, hx + 7 * s, hy - 25 * s],
        radius=max(1, w(1)),
        fill=(226, 232, 240, 140),
    )

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = draw_mark(1024)
    png_path = OUT_DIR / "vassal_icon.png"
    ico_path = OUT_DIR / "vassal_icon.ico"
    # Keep a crisp UI PNG at 512; ICO uses multiple sizes from the 1024 master
    base.resize((512, 512), Image.Resampling.LANCZOS).save(png_path, format="PNG")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [base.resize(sz, Image.Resampling.LANCZOS) for sz in sizes]
    icons[0].save(ico_path, format="ICO", sizes=sizes)
    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
