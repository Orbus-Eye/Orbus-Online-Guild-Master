#!/usr/bin/env python3
"""FASE 9G — Identità visiva delle 27 classi.

Genera per OGNI classe canonica:
  * emblema  → frontend/public/assets/classes/{slug}.svg      (240×240)
  * banner   → frontend/public/assets/classes/{slug}_banner.svg (800×200)

Ogni emblema ha un GLIFO UNICO disegnato a mano per la classe (niente
27 icone fotocopiate): spade incrociate, pugnale nell'ombra, sigillo
arcano, teschio nel cerchio, ingranaggio, rosa dei venti, runa, maschera
coi fili, dadi, pennello, zanna, scudo con fiamma, incudine runica,
radice a spirale, vessillo, drago sulla lancia, alambicco, lira, salice,
tamburo, penna, bilancia, costellazione, mezzaluna sull'occhio, ecc.

Palette e simbolo provengono dal registry (`app.classes.registry`):
la identity map è quindi VERIFICABILE nel codice, non solo negli asset.

Uso:  python scripts/fase9_genera_emblemi_classi.py
Idempotente: riscrive sempre gli stessi file (stessi nomi → zero cambi
di codice FE quando arriverà l'art definitiva).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "x")
os.environ.setdefault("JWT_SECRET", "x" * 32)
os.environ.setdefault("APP_ENV", "test")

from app.classes.registry import CLASS_REGISTRY  # noqa: E402

OUT_DIR = REPO / "frontend" / "public" / "assets" / "classes"


def _shade(hex_color: str, factor: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    if factor >= 1.0:
        t = factor - 1.0
        r, g, b = (round(c + (255 - c) * t) for c in (r, g, b))
    else:
        r, g, b = (round(c * factor) for c in (r, g, b))
    return f"#{min(r, 255):02x}{min(g, 255):02x}{min(b, 255):02x}"


# ── Glifi unici (viewBox 240×240, centro 120,120) ───────────────────
# Ogni funzione riceve (accent, accent_scuro) e ritorna markup SVG.

def g_guerriero(a, d):
    return (f'<g stroke="{a}" stroke-width="10" stroke-linecap="round">'
            f'<line x1="70" y1="170" x2="170" y2="70"/>'
            f'<line x1="70" y1="70" x2="170" y2="170"/></g>'
            f'<g stroke="{d}" stroke-width="6">'
            f'<line x1="80" y1="60" x2="60" y2="80"/>'
            f'<line x1="160" y1="60" x2="180" y2="80"/></g>')


def g_ladro(a, d):
    return (f'<path d="M75 150 Q120 100 165 150 Q120 130 75 150 Z" fill="{d}"/>'
            f'<g transform="rotate(-35 120 105)">'
            f'<rect x="114" y="55" width="12" height="70" rx="4" fill="{a}"/>'
            f'<rect x="104" y="120" width="32" height="10" rx="4" fill="{d}"/>'
            f'</g>')


def g_mago(a, d):
    pts = []
    import math
    for i in range(9):
        ang = math.pi / 2 + i * 2 * math.pi / 9
        pts.append(f"{120 + 52 * math.cos(ang):.1f},{120 - 52 * math.sin(ang):.1f}")
    star = " ".join(pts[i] for i in (0, 4, 8, 3, 7, 2, 6, 1, 5))
    return (f'<polygon points="{star}" fill="none" stroke="{a}" '
            f'stroke-width="5"/><circle cx="120" cy="120" r="10" fill="{d}"/>')


def g_monaco(a, d):
    return (f'<circle cx="120" cy="120" r="46" fill="none" stroke="{d}" '
            f'stroke-width="8" stroke-dasharray="14 9"/>'
            f'<path d="M100 138 q0 -30 20 -34 q20 4 20 34 q-10 10 -20 10 '
            f'q-10 0 -20 -10 Z" fill="{a}"/>')


def g_negromante(a, d):
    return (f'<circle cx="120" cy="120" r="56" fill="none" stroke="{d}" stroke-width="6"/>'
            f'<circle cx="120" cy="108" r="26" fill="{a}"/>'
            f'<rect x="104" y="126" width="32" height="16" rx="6" fill="{a}"/>'
            f'<circle cx="111" cy="104" r="7" fill="{d}"/>'
            f'<circle cx="129" cy="104" r="7" fill="{d}"/>')


def g_cacciatore_del_vuoto(a, d):
    return (f'<ellipse cx="120" cy="120" rx="58" ry="34" fill="none" '
            f'stroke="{a}" stroke-width="6"/>'
            f'<circle cx="120" cy="120" r="16" fill="{a}"/>'
            f'<circle cx="120" cy="120" r="7" fill="{d}"/>'
            f'<circle cx="80" cy="93" r="3" fill="{a}"/>'
            f'<circle cx="164" cy="100" r="2.5" fill="{a}"/>'
            f'<circle cx="150" cy="148" r="3" fill="{a}"/>')


def g_artificiere(a, d):
    import math
    teeth = []
    for i in range(8):
        ang = i * math.pi / 4
        x1 = 120 + 44 * math.cos(ang)
        y1 = 120 + 44 * math.sin(ang)
        teeth.append(f'<rect x="{x1-6:.0f}" y="{y1-10:.0f}" width="12" '
                     f'height="20" rx="3" fill="{a}" '
                     f'transform="rotate({math.degrees(ang):.0f} {x1:.0f} {y1:.0f})"/>')
    return ("".join(teeth)
            + f'<circle cx="120" cy="120" r="34" fill="none" stroke="{a}" stroke-width="10"/>'
            + f'<circle cx="120" cy="120" r="10" fill="{d}"/>')


def g_cartografo(a, d):
    return (f'<g stroke="{a}" stroke-width="5">'
            f'<line x1="120" y1="58" x2="120" y2="182"/>'
            f'<line x1="58" y1="120" x2="182" y2="120"/></g>'
            f'<polygon points="120,70 130,110 120,120 110,110" fill="{a}"/>'
            f'<polygon points="120,170 130,130 120,120 110,130" fill="{d}"/>'
            f'<circle cx="120" cy="120" r="52" fill="none" stroke="{d}" stroke-width="4"/>')


def g_runista(a, d):
    return (f'<g stroke="{a}" stroke-width="9" stroke-linecap="round">'
            f'<line x1="120" y1="60" x2="120" y2="180"/>'
            f'<line x1="120" y1="90" x2="160" y2="65"/>'
            f'<line x1="120" y1="90" x2="80" y2="65"/>'
            f'<line x1="120" y1="140" x2="162" y2="168"/></g>'
            f'<circle cx="120" cy="120" r="58" fill="none" stroke="{d}" '
            f'stroke-width="4" stroke-dasharray="6 8"/>')


def g_burattinaio(a, d):
    return (f'<g stroke="{d}" stroke-width="3">'
            f'<line x1="90" y1="52" x2="96" y2="108"/>'
            f'<line x1="120" y1="48" x2="120" y2="104"/>'
            f'<line x1="150" y1="52" x2="144" y2="108"/></g>'
            f'<rect x="78" y="42" width="84" height="10" rx="4" fill="{a}"/>'
            f'<path d="M88 118 q32 -22 64 0 q4 34 -32 50 q-36 -16 -32 -50 Z" fill="{a}"/>'
            f'<circle cx="106" cy="132" r="6" fill="{d}"/>'
            f'<circle cx="134" cy="132" r="6" fill="{d}"/>'
            f'<path d="M106 152 q14 10 28 0" stroke="{d}" stroke-width="4" fill="none"/>')


def g_giocatore(a, d):
    return (f'<g transform="rotate(-12 100 122)">'
            f'<rect x="72" y="94" width="56" height="56" rx="8" fill="{a}"/>'
            f'<circle cx="86" cy="108" r="5" fill="{d}"/>'
            f'<circle cx="100" cy="122" r="5" fill="{d}"/>'
            f'<circle cx="114" cy="136" r="5" fill="{d}"/></g>'
            f'<g transform="rotate(14 148 124)">'
            f'<rect x="120" y="96" width="56" height="56" rx="8" fill="{d}"/>'
            f'<circle cx="134" cy="110" r="5" fill="{a}"/>'
            f'<circle cx="162" cy="110" r="5" fill="{a}"/>'
            f'<circle cx="134" cy="138" r="5" fill="{a}"/>'
            f'<circle cx="162" cy="138" r="5" fill="{a}"/></g>')


def g_pittore(a, d):
    return (f'<g transform="rotate(35 120 120)">'
            f'<rect x="112" y="52" width="16" height="80" rx="6" fill="{d}"/>'
            f'<path d="M112 132 h16 l-4 26 q-4 8 -8 0 Z" fill="{a}"/></g>'
            f'<path d="M138 168 q10 22 -6 26 q10 -12 -2 -20 Z" fill="{a}"/>')


def g_cacciatore_del_sangue(a, d):
    return (f'<path d="M96 60 q34 30 30 78 q-4 30 -18 42 q6 -28 -4 -52 '
            f'q-16 -30 -8 -68 Z" fill="{a}"/>'
            f'<path d="M150 128 q16 22 0 40 q-16 -18 0 -40 Z" fill="{d}"/>')


def g_paladino(a, d):
    return (f'<path d="M120 52 q34 14 52 12 q0 74 -52 122 q-52 -48 -52 -122 '
            f'q18 2 52 -12 Z" fill="none" stroke="{a}" stroke-width="8"/>'
            f'<path d="M120 92 q14 22 0 34 q-8 -6 -8 -16 q0 6 4 10 '
            f'q-10 14 -12 26 q28 4 32 -18 q2 -20 -16 -36 Z" fill="{a}"/>')


def g_cacciatore_di_mostri(a, d):
    return (f'<path d="M84 96 q36 -26 72 0 l-12 34 q-24 18 -48 0 Z" fill="{a}"/>'
            f'<path d="M96 130 l8 18 l8 -14 Z" fill="{d}"/>'
            f'<path d="M144 130 l-8 18 l-8 -14 Z" fill="{d}"/>'
            f'<line x1="60" y1="180" x2="180" y2="60" stroke="{d}" stroke-width="8" '
            f'stroke-linecap="round"/>'
            f'<polygon points="180,60 168,64 176,72" fill="{d}"/>')


def g_fabbro_arcano(a, d):
    return (f'<path d="M64 108 h112 v22 q-36 8 -56 30 h-16 q-8 -18 -40 -22 Z" fill="{a}"/>'
            f'<rect x="102" y="160" width="36" height="14" rx="4" fill="{d}"/>'
            f'<path d="M112 84 l8 -18 l8 18 l-8 14 Z" fill="{d}"/>')


def g_parassita(a, d):
    return (f'<path d="M120 60 q-44 24 -36 68 q6 34 36 52 q30 -18 36 -52 '
            f'q8 -44 -36 -68 Z" fill="none" stroke="{d}" stroke-width="6"/>'
            f'<path d="M120 84 q-20 14 -14 38 q4 20 14 30 q10 -10 14 -30 '
            f'q6 -24 -14 -38 Z" fill="{a}"/>'
            f'<path d="M120 154 q-2 14 -12 22 M120 154 q2 14 12 22" '
            f'stroke="{a}" stroke-width="5" fill="none"/>')


def g_cavaliere_della_morte(a, d):
    return (f'<path d="M92 100 q0 -34 28 -34 q28 0 28 34 v34 q-14 12 -28 12 '
            f'q-14 0 -28 -12 Z" fill="{a}"/>'
            f'<rect x="100" y="104" width="14" height="10" rx="4" fill="{d}"/>'
            f'<rect x="126" y="104" width="14" height="10" rx="4" fill="{d}"/>'
            f'<line x1="120" y1="46" x2="120" y2="70" stroke="{d}" stroke-width="6"/>'
            f'<path d="M120 46 h44 l-10 12 h-34 Z" fill="{d}"/>')


def g_cavaliere_di_draghi(a, d):
    return (f'<line x1="120" y1="52" x2="120" y2="188" stroke="{d}" '
            f'stroke-width="8" stroke-linecap="round"/>'
            f'<polygon points="120,40 112,60 128,60" fill="{d}"/>'
            f'<path d="M120 84 q-44 8 -40 44 q4 28 40 32 q-20 -14 -20 -36 '
            f'q0 -26 20 -40 Z" fill="{a}"/>'
            f'<path d="M120 84 q30 10 26 34 l-14 -6 q6 18 -12 32 '
            f'q14 -30 0 -60 Z" fill="{a}"/>')


def g_alchimista(a, d):
    return (f'<path d="M108 58 h24 v34 l28 54 q6 26 -20 30 h-40 q-26 -4 -20 -30 '
            f'l28 -54 Z" fill="none" stroke="{a}" stroke-width="7"/>'
            f'<path d="M94 138 h52 l8 16 q2 14 -14 16 h-40 q-16 -2 -14 -16 Z" fill="{a}"/>'
            f'<circle cx="112" cy="128" r="5" fill="{d}"/>'
            f'<circle cx="130" cy="118" r="4" fill="{d}"/>')


def g_bardo(a, d):
    return (f'<path d="M92 66 q-20 56 28 108 q48 -52 28 -108 q-8 22 -28 22 '
            f'q-20 0 -28 -22 Z" fill="none" stroke="{a}" stroke-width="7"/>'
            f'<g stroke="{a}" stroke-width="4">'
            f'<line x1="108" y1="98" x2="108" y2="158"/>'
            f'<line x1="132" y1="98" x2="132" y2="158"/></g>'
            f'<line x1="120" y1="96" x2="120" y2="128" stroke="{d}" stroke-width="4"/>'
            f'<path d="M120 128 q10 8 0 16" stroke="{d}" stroke-width="4" fill="none"/>')


def g_druido(a, d):
    return (f'<line x1="120" y1="188" x2="120" y2="96" stroke="{d}" stroke-width="8"/>'
            f'<path d="M120 96 q-36 -4 -48 -34 q34 -4 48 18 q14 -22 48 -18 '
            f'q-12 30 -48 34 Z" fill="{a}"/>'
            f'<path d="M120 128 q-22 0 -30 -16 q20 -2 30 10 q10 -12 30 -10 '
            f'q-8 16 -30 16 Z" fill="{a}"/>'
            f'<path d="M96 188 q24 -10 48 0" stroke="{d}" stroke-width="6" fill="none"/>')


def g_sciamano(a, d):
    return (f'<circle cx="120" cy="120" r="44" fill="none" stroke="{a}" stroke-width="8"/>'
            f'<g stroke="{d}" stroke-width="5">'
            f'<line x1="88" y1="152" x2="152" y2="88"/>'
            f'<line x1="88" y1="88" x2="152" y2="152"/></g>'
            f'<path d="M164 64 q10 18 -4 30 q-2 -16 -8 -22 Z" fill="{a}"/>')


def g_cronista(a, d):
    return (f'<path d="M84 172 l64 -104 q10 -12 18 -4 q8 8 -4 18 l-64 104 '
            f'l-22 8 Z" fill="{a}"/>'
            f'<path d="M84 172 l8 -14 l14 8 l-14 14 Z" fill="{d}"/>'
            f'<line x1="78" y1="188" x2="162" y2="188" stroke="{d}" stroke-width="5"/>')


def g_mercante(a, d):
    return (f'<line x1="120" y1="56" x2="120" y2="170" stroke="{a}" stroke-width="7"/>'
            f'<line x1="72" y1="80" x2="168" y2="80" stroke="{a}" stroke-width="7"/>'
            f'<path d="M72 80 l-18 40 q18 14 36 0 Z" fill="none" stroke="{a}" stroke-width="5"/>'
            f'<path d="M168 80 l-18 40 q18 14 36 0 Z" fill="none" stroke="{a}" stroke-width="5"/>'
            f'<rect x="96" y="170" width="48" height="10" rx="4" fill="{d}"/>')


def g_astrologo(a, d):
    stars = (
        (78, 88, 4), (108, 66, 3), (142, 78, 5), (166, 108, 3),
        (150, 146, 4), (112, 158, 3), (84, 132, 3),
    )
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{a}"/>' for x, y, r in stars
    )
    path = "M78 88 L108 66 L142 78 L166 108 L150 146 L112 158 L84 132 Z"
    return (f'<path d="{path}" fill="none" stroke="{d}" stroke-width="3" '
            f'stroke-dasharray="5 6"/>{dots}'
            f'<circle cx="120" cy="112" r="8" fill="{a}"/>')


def g_sognatore(a, d):
    return (f'<path d="M148 64 a52 52 0 1 0 24 74 a44 44 0 1 1 -24 -74 Z" fill="{a}"/>'
            f'<path d="M96 138 q22 -18 44 0 q-22 12 -44 0 Z" fill="{d}"/>')


GLYPHS = {
    "guerriero": g_guerriero,
    "ladro": g_ladro,
    "mago": g_mago,
    "monaco": g_monaco,
    "negromante": g_negromante,
    "cacciatore_del_vuoto": g_cacciatore_del_vuoto,
    "artificiere": g_artificiere,
    "cartografo": g_cartografo,
    "runista": g_runista,
    "burattinaio": g_burattinaio,
    "giocatore_d_azzardo": g_giocatore,
    "pittore": g_pittore,
    "cacciatore_del_sangue": g_cacciatore_del_sangue,
    "paladino": g_paladino,
    "cacciatore_di_mostri": g_cacciatore_di_mostri,
    "fabbro_arcano": g_fabbro_arcano,
    "parassita": g_parassita,
    "cavaliere_della_morte": g_cavaliere_della_morte,
    "cavaliere_di_draghi": g_cavaliere_di_draghi,
    "alchimista": g_alchimista,
    "bardo": g_bardo,
    "druido": g_druido,
    "sciamano": g_sciamano,
    "cronista": g_cronista,
    "mercante": g_mercante,
    "astrologo": g_astrologo,
    "sognatore": g_sognatore,
}

ROLE_RING = {"DPS": "#f87171", "TANK": "#38bdf8", "HEALER": "#34d399"}


def emblem_svg(definition) -> str:
    base, accent = definition.palette
    dark = _shade(base, 0.55)
    accent_dark = _shade(accent, 0.55)
    ring = ROLE_RING[definition.class_role]
    glyph = GLYPHS[definition.class_id](accent, accent_dark)
    return f"""<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{definition.class_name}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="38%" r="75%">
      <stop offset="0%" stop-color="{_shade(base, 1.25)}"/>
      <stop offset="70%" stop-color="{base}"/>
      <stop offset="100%" stop-color="{dark}"/>
    </radialGradient>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <circle cx="120" cy="120" r="112" fill="url(#bg)"/>
  <circle cx="120" cy="120" r="112" fill="none" stroke="{ring}" stroke-width="6"/>
  <circle cx="120" cy="120" r="100" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="4 7" opacity="0.7"/>
  <g filter="url(#glow)">{glyph}</g>
</svg>
"""


def banner_svg(definition) -> str:
    base, accent = definition.palette
    dark = _shade(base, 0.45)
    ring = ROLE_RING[definition.class_role]
    glyph = GLYPHS[definition.class_id](accent, _shade(accent, 0.55))
    return f"""<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{definition.class_name}">
  <defs>
    <linearGradient id="bb" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="45%" stop-color="{base}"/>
      <stop offset="100%" stop-color="{_shade(base, 0.7)}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="200" fill="url(#bb)"/>
  <g transform="translate(60 -20) scale(1.0)" opacity="0.9">{glyph}</g>
  <text x="320" y="92" font-family="Georgia, serif" font-size="44"
        fill="{_shade(accent, 1.3)}" font-weight="bold">{definition.class_name}</text>
  <text x="322" y="132" font-family="Georgia, serif" font-size="20"
        fill="{accent}" opacity="0.9">{definition.class_identity}</text>
  <rect x="320" y="148" width="150" height="26" rx="4" fill="none"
        stroke="{ring}" stroke-width="2"/>
  <text x="334" y="166" font-family="monospace" font-size="15"
        fill="{ring}">{definition.class_role}</text>
  <rect x="6" y="6" width="788" height="188" fill="none"
        stroke="{accent}" stroke-width="2" opacity="0.5"/>
</svg>
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for definition in CLASS_REGISTRY.values():
        (OUT_DIR / f"{definition.class_id}.svg").write_text(
            emblem_svg(definition), encoding="utf-8")
        (OUT_DIR / f"{definition.class_id}_banner.svg").write_text(
            banner_svg(definition), encoding="utf-8")
        written += 2
    print(f"scritti {written} SVG in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
