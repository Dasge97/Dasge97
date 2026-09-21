"""Generate the stack panel and the compact project cards as SVGs.

Icons come from Simple Icons (CC0); the Space Mono font is embedded so the
SVGs render the same inside GitHub's <img> on any system.

Usage: python tools/make_cards.py
"""
import json
import pathlib
import re
import urllib.request
from xml.sax.saxutils import escape

import inline_fonts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.32.0"

BG, BORDER, CHIP, TEXT, MUTED, GREEN = "#0f1714", "#2b4a3d", "#13201b", "#e6edf3", "#8fb3a5", "#22c55e"
FONT = "'Space Mono', monospace"
CHAR = 0.6125  # Space Mono advance width, in em

# (English label, Spanish label, [(chip text, simple-icons slug or None)])
STACK = [
    ("languages", "lenguajes", [("PHP", "php"), ("TypeScript", "typescript"), ("JavaScript", "javascript"),
                                ("Python", "python"), ("Go", "go"), ("Rust", "rust"), ("Dart", "dart")]),
    ("frameworks", "frameworks", [("Symfony", "symfony"), ("Node.js", "nodedotjs"), ("Express", "express"),
                                  ("Vue", "vuedotjs"), ("Flutter", "flutter")]),
    ("ai", "ia", [("Claude Code", "claude"), ("ChatGPT", None), ("OpenCode", "opencode"), ("Ollama", "ollama"),
                  ("Multi-agent", None), ("RAG", None), ("Voice agents", None)]),
    ("data & infra", "datos e infra", [("MySQL", "mysql"), ("PostgreSQL", "postgresql"), ("Docker", "docker"),
                                       ("Linux", "linux"), ("Traefik", "traefikproxy"), ("n8n", "n8n"), ("Git", "git")]),
    ("integrations", "integraciones", [("Odoo", "odoo"), ("Stripe", "stripe"),
                                       ("Telegram", "telegram"), ("WhatsApp", "whatsapp")]),
]

# GitHub's language colours.
LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "PHP": "#4F5D95",
               "Python": "#3572A5", "Go": "#00ADD8"}

# (repo, language, public, English line, Spanish line). Private repos get no link.
PROJECTS = [
    ("codehive-factory", "TypeScript", True, "Agents that build and fix projects",
     "Agentes que construyen y corrigen código"),
    ("pocket-terminal", "JavaScript", True, "My PC's terminal, on my phone",
     "La terminal de mi PC, en el móvil"),
    ("podcaster", "PHP", False, "Automated vertical video studio",
     "Estudio automático de vídeo vertical"),
    ("centralita-ia", "TypeScript", False, "AI voice agent for phone orders",
     "Pedidos por teléfono con agente de voz"),
    ("claude-monitoring-rainmeter", "JavaScript", True, "Claude Code sessions on my desktop",
     "Sesiones de Claude Code en el escritorio"),
    ("ministudio", "PHP", False, "Instagram posts about current news",
     "Posts de Instagram sobre la actualidad"),
]


def fetch(url):
    with urllib.request.urlopen(url) as res:
        return res.read().decode("utf-8")


def icon_colors():
    return {i["slug"]: "#" + i["hex"] for i in json.loads(fetch(ICONS + "/data/simple-icons.json"))}


def readable(hex_color):
    """Brand colours too dark for the dark background become light grey."""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return hex_color if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.28 else "#c9d1d9"


def text_width(text, size):
    return len(text) * size * CHAR


def svg_doc(width, height, label, body, style=""):
    chars = "".join(sorted(set(re.sub(r"<[^>]+>", "", body)))) + "$~/"
    fonts = inline_fonts.face_css("Space%20Mono:wght@400;700", chars)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{fonts}{style}</style>{body}</svg>')


def stack_svg(lang, colors, paths):
    width, left, chip_h, gap, size = 880, 128, 24, 6, 11
    rows, y = [], 12
    for index, (en, es, chips) in enumerate(STACK):
        label = (en if lang == "en" else es) + "/"
        parts = [f'<text x="16" y="{y + 16}" fill="{GREEN}" font-size="{size}" font-family="{FONT}">{escape(label)}</text>']
        x = left
        for name, slug in chips:
            pad = 26 if slug else 10
            w = pad + text_width(name, size) + 9
            parts.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{chip_h}" rx="5" fill="{CHIP}" stroke="{BORDER}"/>')
            if slug:
                parts.append(f'<svg x="{x + 8:.0f}" y="{y + 6}" width="12" height="12" viewBox="0 0 24 24">'
                             f'<path fill="{readable(colors[slug])}" d="{paths[slug]}"/></svg>')
            parts.append(f'<text x="{x + pad:.0f}" y="{y + 16}" fill="{TEXT}" font-size="{size}" font-family="{FONT}">{escape(name)}</text>')
            x += w + gap
        assert x < width, f"{en} row is too wide"
        rows.append(f'<g class="row" style="animation-delay:{0.1 + index * 0.1:.2f}s">{"".join(parts)}</g>')
        y += chip_h + gap
    height = y + 6
    body = f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>' + "".join(rows)
    style = ("@keyframes in{from{opacity:0}to{opacity:1}}.row{opacity:0;animation:in .5s ease-out forwards}"
             "@media (prefers-reduced-motion:reduce){.row{opacity:1;animation:none}}")
    label = "Stack: " + ", ".join(n for _, _, chips in STACK for n, _ in chips)
    return svg_doc(width, height, label, body, style)


def card_svg(repo, language, public, line):
    width, height = 290, 56
    corner = (f'<path d="M270 20 L279 11 M272 11 H279 V18" stroke="{GREEN}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
              if public else
              f'<text x="278" y="19" text-anchor="end" fill="{MUTED}" font-size="9" font-family="{FONT}">private</text>')
    body = (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>'
            f'<circle cx="16" cy="19" r="4" fill="{LANG_COLORS[language]}"/>'
            f'<text x="26" y="23" fill="{TEXT}" font-size="12" font-weight="700" font-family="{FONT}">{escape(repo)}</text>'
            + corner +
            f'<text x="12" y="43" fill="{MUTED}" font-size="10.5" font-family="{FONT}">{escape(line)}</text>')
    assert 26 + text_width(repo, 12) < 262 and 12 + text_width(line, 10.5) < width - 8, repo
    return svg_doc(width, height, f"{repo} ({language}): {line}", body)


def main():
    colors = icon_colors()
    slugs = {s for _, _, chips in STACK for _, s in chips if s}
    paths = {s: re.search(r' d="([^"]+)"', fetch(f"{ICONS}/icons/{s}.svg")).group(1) for s in slugs}
    for lang, suffix in (("en", ""), ("es", ".es")):
        (OUT / f"stack{suffix}.svg").write_text(stack_svg(lang, colors, paths), encoding="utf-8", newline="")
    for old in OUT.glob("p-*.svg"):
        old.unlink()
    for repo, language, public, en, es in PROJECTS:
        (OUT / f"p-{repo}.svg").write_text(card_svg(repo, language, public, en), encoding="utf-8", newline="")
        (OUT / f"p-{repo}.es.svg").write_text(card_svg(repo, language, public, es), encoding="utf-8", newline="")
    print("stack + %d project cards" % len(PROJECTS))


if __name__ == "__main__":
    main()
