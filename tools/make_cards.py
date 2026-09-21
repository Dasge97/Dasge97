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
    ("ai", "ia", [("Claude Code", "claude"), ("Ollama", "ollama"), ("Multi-agent", None),
                  ("RAG", None), ("Voice agents", None)]),
    ("data", "datos", [("MySQL", "mysql"), ("PostgreSQL", "postgresql")]),
    ("infra", "infra", [("Docker", "docker"), ("Linux", "linux"), ("Traefik", "traefikproxy"),
                        ("n8n", "n8n"), ("Git", "git")]),
    ("integrations", "integraciones", [("Odoo", "odoo"), ("Stripe", "stripe"),
                                       ("Telegram", "telegram"), ("WhatsApp", "whatsapp")]),
]

# GitHub's language colours.
LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "PHP": "#4F5D95",
               "Python": "#3572A5", "Go": "#00ADD8"}

# (repo, language, English description lines, Spanish description lines)
PROJECTS = [
    ("codehive-factory", "TypeScript", ["Coding agents that build, review", "and fix projects together."],
     ["Agentes que construyen, revisan", "y corrigen proyectos en equipo."]),
    ("pocket-terminal", "JavaScript", ["Mobile web terminal to control my PC", "and run Claude Code from my phone."],
     ["Terminal web para el móvil: controlo", "mi PC y uso Claude Code desde fuera."]),
    ("odrys-cli", "Go", ["AI-assisted dev client for the", "terminal that orchestrates agents."],
     ["Cliente de desarrollo con IA para la", "terminal que orquesta agentes."]),
    ("auto-order", "PHP", ["Voice agents that take phone orders", "and log them in your system."],
     ["Agentes de voz que recogen pedidos por", "teléfono y los apuntan en tu sistema."]),
    ("pdf2audio", "Python", ["PDF to audiobook, 100% local and free,", "with optional EN-ES translation."],
     ["PDF a audiolibro, 100% local y gratis,", "con traducción EN-ES opcional."]),
    ("claude-monitoring-rainmeter", "JavaScript", ["Desktop panel with the status of", "every Claude Code session."],
     ["Panel de escritorio con el estado de", "cada sesión de Claude Code."]),
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
    width, left, chip_h, gap = 880, 168, 30, 8
    rows, y = [], 56
    for index, (en, es, chips) in enumerate(STACK):
        label = (en if lang == "en" else es) + "/"
        parts = [f'<text x="24" y="{y + 20}" fill="{GREEN}" font-size="13" font-family="{FONT}">{escape(label)}</text>']
        x = left
        for name, slug in chips:
            w = (34 if slug else 14) + text_width(name, 13) + 12
            if x + w > width - 24:
                x, y = left, y + chip_h + gap
            parts.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{chip_h}" rx="6" fill="{CHIP}" stroke="{BORDER}"/>')
            if slug:
                parts.append(f'<svg x="{x + 10}" y="{y + 7}" width="16" height="16" viewBox="0 0 24 24">'
                             f'<path fill="{readable(colors[slug])}" d="{paths[slug]}"/></svg>')
            tx = x + (34 if slug else 14)
            parts.append(f'<text x="{tx}" y="{y + 20}" fill="{TEXT}" font-size="13" font-family="{FONT}">{escape(name)}</text>')
            x += w + gap
        rows.append(f'<g class="row" style="animation-delay:{0.15 + index * 0.12:.2f}s">{"".join(parts)}</g>')
        y += chip_h + 16
    height = y + 8
    title = "$ ls ~/stack"
    body = (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
            f'<path d="M0.5 38.5H{width - 0.5}" stroke="{BORDER}"/>'
            + "".join(f'<circle cx="{22 + i * 18}" cy="19" r="5" fill="{c}"/>'
                      for i, c in enumerate(["#3b5a4d", "#3b5a4d", "#3b5a4d"]))
            + f'<text x="84" y="24" fill="{MUTED}" font-size="12" font-family="{FONT}">{title}</text>'
            f'<rect class="caret" x="{84 + text_width(title, 12) + 4:.0f}" y="13" width="7" height="14" fill="{GREEN}"/>'
            + "".join(rows))
    style = ("@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
             ".row{opacity:0;animation:in .5s ease-out forwards}"
             "@keyframes blink{50%{opacity:0}}.caret{animation:blink 1.1s steps(1) infinite}"
             "@media (prefers-reduced-motion:reduce){.row{opacity:1;animation:none}.caret{animation:none}}")
    label = "Stack: " + ", ".join(n for _, _, chips in STACK for n, _ in chips)
    return svg_doc(width, height, label, body, style)


def card_svg(repo, language, lines):
    width, height = 440, 124
    arrow = f'<path d="M404 34 L418 20 M407 20 H418 V31" stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round"/>'
    body = (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
            f'<circle cx="26" cy="27" r="5" fill="{LANG_COLORS[language]}"/>'
            f'<text x="38" y="31" fill="{MUTED}" font-size="12" font-family="{FONT}">{language}</text>'
            + arrow +
            f'<text x="20" y="64" fill="{TEXT}" font-size="18" font-weight="700" font-family="{FONT}">{escape(repo)}</text>'
            + "".join(f'<text x="20" y="{90 + i * 18}" fill="{MUTED}" font-size="12" font-family="{FONT}">{escape(l)}</text>'
                      for i, l in enumerate(lines)))
    return svg_doc(width, height, f"{repo}: {' '.join(lines)}", body)


def main():
    colors = icon_colors()
    slugs = {s for _, _, chips in STACK for _, s in chips if s}
    paths = {s: re.search(r' d="([^"]+)"', fetch(f"{ICONS}/icons/{s}.svg")).group(1) for s in slugs}
    for lang, suffix in (("en", ""), ("es", ".es")):
        (OUT / f"stack{suffix}.svg").write_text(stack_svg(lang, colors, paths), encoding="utf-8", newline="")
    for repo, language, en, es in PROJECTS:
        (OUT / f"p-{repo}.svg").write_text(card_svg(repo, language, en), encoding="utf-8", newline="")
        (OUT / f"p-{repo}.es.svg").write_text(card_svg(repo, language, es), encoding="utf-8", newline="")
    print("stack + %d project cards" % len(PROJECTS))


if __name__ == "__main__":
    main()
