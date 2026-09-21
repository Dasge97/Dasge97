"""Build the README's animated SVGs from the raw wordanimator.com exports.

Raw exports live in assets/src/ (downloaded from wordanimator.com with
"Transparent background" checked). For each one this script:
  - embeds its Google Fonts so it renders inside GitHub's <img> (inline_fonts);
  - for Teletype headings, swaps the pale green for one readable on both
    GitHub themes and crops the empty space around the text.

Usage: python tools/build_assets.py
"""
import pathlib
import re
import tempfile

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


def tune_matrix(svg):
    """Crop to the band the letters scroll through, so the text fills the width."""
    width = float(re.search(r'viewBox="0 0 ([0-9.]+) [0-9.]+"', svg).group(1))
    return re.sub(r'viewBox="[^"]+"', f'viewBox="100 50 {width - 200:.0f} 130"', svg, count=1)


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
