"""Build the README's animated SVGs from the raw wordanimator.com exports.

Raw exports live in assets/src/ (downloaded from wordanimator.com with
"Transparent background" checked). For each one this script:
  - embeds its Google Fonts so it renders inside GitHub's <img> (inline_fonts);
  - for Teletype headings, swaps the pale green for one readable on both
    GitHub themes and crops the empty space around the text.

Usage: python tools/build_assets.py
"""
import io
import pathlib
import re
import tempfile
import urllib.request

from fontTools.ttLib import TTFont

import inline_fonts

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src"
OUT = ROOT / "assets"

# Pale greens from the export -> greens with enough contrast on white and on #0d1117.
TELETYPE_COLORS = {"#86efac": "#16a34a", "#4ade80": "#22c55e"}


def tune_teletype(svg):
    for old, new in TELETYPE_COLORS.items():
        svg = svg.replace(f'fill="{old}"', f'fill="{new}"')
    # Letters are centred on their x with a fixed advance; the caret starts
    # before the first letter and slides right by translateX.
    xs = [float(x) for x in re.findall(r'<text class="tt-l"[^>]* x="([0-9.]+)"', svg)]
    caret_x = float(re.search(r'class="tt-caret" x="([0-9.]+)"', svg).group(1))
    advance = float(re.search(r"translateX\(([0-9.]+)px\)", svg).group(1))
    left = caret_x - 8
    right = max(xs[-1] + 34, caret_x + advance + 22)
    return re.sub(r'viewBox="[^"]+"', f'viewBox="{left:.0f} 58 {right - left:.0f} 112"', svg, count=1)


def orbitron_advances(size):
    """Advance width of each Orbitron Black glyph at `size`, keyed by character."""
    # Without a browser user agent Google Fonts serves TTF, which fontTools reads as is.
    css = urllib.request.urlopen("https://fonts.googleapis.com/css2?family=Orbitron:wght@900").read().decode("utf-8")
    font = TTFont(io.BytesIO(urllib.request.urlopen(re.search(r"url\((https://[^)]+)\)", css).group(1)).read()))
    scale = size / font["head"].unitsPerEm
    return {chr(code): font["hmtx"][glyph][0] * scale for code, glyph in font.getBestCmap().items()}


def tune_matrix(svg):
    """Space the letters by their real width, then crop so the text fills the width.

    The export puts every letter in an 80px column, which leaves an I floating
    in empty space and clips wide letters like W and M.
    """
    text = re.search(r'aria-label="Matrix decode text for ([^"]+)"', svg).group(1)
    advances = orbitron_advances(104)
    x, columns = 120.0, []
    for char in text:
        if char == " ":
            x += 44
            continue
        columns.append((x, advances.get(char, 80)))
        x += advances.get(char, 80) + 6
    ids = [int(i) for i in re.findall(r'<clipPath id="mx-clip-(\d+)">', svg)]
    assert len(ids) == len(columns), "letter columns do not match the text"
    for clip_id, (left, width) in zip(ids, columns):
        old = re.search(rf'<clipPath id="mx-clip-{clip_id}"><rect x="([0-9.]+)"', svg).group(1)
        old_center = float(old) + 40
        svg = svg.replace(f'<clipPath id="mx-clip-{clip_id}"><rect x="{old}" y="54" width="80"',
                          f'<clipPath id="mx-clip-{clip_id}"><rect x="{left - 3:.1f}" y="54" width="{width + 6:.1f}"')
        start = svg.index(f'url(#mx-clip-{clip_id})"')
        end = svg.index("</text>", start)
        column = svg[start:end].replace(f'x="{old_center:g}"', f'x="{left + width / 2:.1f}"')
        svg = svg[:start] + column + svg[end:]
    return re.sub(r'viewBox="[^"]+"', f'viewBox="100 50 {x - 6 - 100 + 20:.0f} 130"', svg, count=1)


def main():
    for src in sorted(SRC.glob("*.svg")):
        with tempfile.TemporaryDirectory() as tmp:
            fixed = pathlib.Path(tmp) / src.name
            inline_fonts.main(src, fixed)
            svg = fixed.read_text(encoding="utf-8")
        if "tt-caret" in svg:
            svg = tune_teletype(svg)
        elif "mx-scroll" in svg:
            svg = tune_matrix(svg)
        (OUT / src.name).write_text(svg, encoding="utf-8", newline="")
        print(f"{src.name}: {len(svg.encode()) // 1024} KB")


if __name__ == "__main__":
    main()
