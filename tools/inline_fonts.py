"""Make a wordanimator.com SVG export render on GitHub.

GitHub shows README images through <img>, which blocks external resources,
so the Google Fonts @import in the export never loads. This script replaces
that @import with @font-face rules whose fonts are embedded as base64,
subset to the characters the SVG actually uses.

Usage: python tools/inline_fonts.py input.svg output.svg
"""
import base64
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# A browser user agent makes Google Fonts answer with woff2.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as res:
        return res.read()


def used_chars(svg):
    """Every character drawn by a text element (tails included)."""
    chars = set()
    for el in ET.fromstring(svg).iter():
        chars.update(el.text or "")
        chars.update(el.tail or "")
    return "".join(sorted(c for c in chars if not c.isspace() or c == " "))


def face_css(family_param, chars):
    """@font-face CSS for one Google Fonts family, fonts embedded."""
    base = "https://fonts.googleapis.com/css2?family=" + family_param
    try:
        css = fetch(base + "&text=" + urllib.parse.quote(chars)).decode("utf-8")
        fonts = {u: fetch(u) for u in re.findall(r"url\((https://[^)]+)\)", css)}
    except urllib.error.HTTPError:
        # Google refuses a subset with characters the font lacks; keep the ones it has.
        latin_chars = "".join(c for c in chars if ord(c) < 0x250) or "A"
        css = fetch(base + "&text=" + urllib.parse.quote(latin_chars)).decode("utf-8")
        fonts = {u: fetch(u) for u in re.findall(r"url\((https://[^)]+)\)", css)}
    for url, data in fonts.items():
        css = css.replace(url, "data:font/woff2;base64," + base64.b64encode(data).decode("ascii"))
    return css


def main(src, dst):
    svg = open(src, encoding="utf-8", newline="").read()
    chars = used_chars(svg)
    # Fallback families never render once the first one is embedded, so skip them.
    first_families = {m.strip().strip("'\"") for m in
                      re.findall(r"font-family(?:=\"|:\s*)\s*([^,;\"]+)", svg)}
    for match in re.findall(r"@import url\(['\"]?([^'\")]+)['\"]?\);?", svg):
        query = urllib.parse.urlparse(match.replace("&amp;", "&")).query
        params = [urllib.parse.unquote_plus(p) for p in re.findall(r"family=([^&]+)", query)]
        faces = [face_css(urllib.parse.quote(param, safe=":;@,+"), chars)
                 for param in params if param.split(":")[0] in first_families]
        pattern = r"@import url\(['\"]?" + re.escape(match) + r"['\"]?\);?"
        svg = re.sub(pattern, lambda _: "\n".join(faces), svg, count=1)
    if "fonts.googleapis.com" in svg:
        sys.exit(f"{src}: a Google Fonts reference is still there")
    open(dst, "w", encoding="utf-8", newline="").write(svg)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
