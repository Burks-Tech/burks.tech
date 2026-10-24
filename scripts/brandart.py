"""Render burks.tech static brand art: favicon.ico, apple-touch-icon.png and the Open Graph base images."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAPER = (247, 242, 234)
INK = (36, 33, 29)
TEXT = (42, 39, 35)
RULE = (228, 219, 205)
ACCENT = (194, 65, 12)
ACCENT_ON_INK = (242, 140, 78)


def monogram(size, serif):
    """'b.' on an ink tile, drawn at 4x and downsampled for clean edges."""
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=INK)
    font = ImageFont.truetype(serif, int(s * 0.78))
    l, t, r, b = d.textbbox((0, 0), "b", font=font, anchor="ls")
    dot = s * 0.085
    total = (r - l) + dot * 2.6
    x = (s - total) / 2 - l
    baseline = s * 0.76
    d.text((x, baseline), "b", font=font, fill=PAPER, anchor="ls")
    cx = x + r + dot * 1.5
    d.ellipse([cx - dot, baseline - 2 * dot, cx + dot, baseline], fill=ACCENT_ON_INK)
    return img.resize((size, size), Image.LANCZOS)


def og_base(path_out, mono):
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(mono, 30)
    x, y = 80, 72
    d.text((x, y), "burks", font=font, fill=TEXT)
    x += d.textlength("burks", font=font)
    d.text((x, y), ".", font=font, fill=ACCENT)
    x += d.textlength(".", font=font)
    d.text((x, y), "tech", font=font, fill=TEXT)
    d.line([(80, 520), (1120, 520)], fill=RULE, width=2)
    d.ellipse([1104, 74, 1120, 90], fill=ACCENT)
    img.save(path_out, optimize=True)


def main(repo, fonts):
    repo, fonts = Path(repo), Path(fonts)
    serif = str(fonts / "newsreader-500.ttf")
    mono = str(fonts / "jetbrains-mono-500.ttf")
    big = monogram(256, serif)
    big.save(repo / "static" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    touch = Image.new("RGB", (180, 180), INK)
    icon = monogram(180, serif)
    touch.paste(icon, (0, 0), icon)
    touch.save(repo / "static" / "apple-touch-icon.png", optimize=True)
    og_base(repo / "assets" / "og" / "base.png", mono)
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
