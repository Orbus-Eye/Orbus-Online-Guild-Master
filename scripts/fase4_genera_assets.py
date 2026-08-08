"""FASE 4 + 8F (2026-08-08) — Generatore di asset fantasy (SVG), v2.

Genera in `frontend/public/assets/`:
  * avatars/{race_slug}_{male|female}.svg  (50 razze × 2) + default.svg
    — ritratto stilizzato: volto con occhi/sopracciglia/bocca, collo,
    spallacci corazzati con finitura e emblema, capigliatura per
    genere, luci/ombre, tratti distintivi per gruppo lore (orecchie
    elfiche, corna, zanne, aureola, ...).
  * themes/{theme}.svg — banner per famiglia visiva dei dungeon
    (cielo stellato, tre quinte di paesaggio, glifo con bagliore,
    cornice ornamentale).
  * raids/{slug}.svg — banner per i 4 raid.
  * banners/{section}.svg — banner delle sezioni principali.

v2 (FASE 8F): resta art procedurale — presentabile, ma quando arriverà
l'art definitiva basterà sostituire i file mantenendo gli stessi nomi
(nessun cambio di codice). Manifest: memory/fase4_asset_manifest.md

Esecuzione (da root repo):  python scripts/fase4_genera_assets.py
Idempotente: sovrascrive sempre gli stessi file.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend" / "public" / "assets"

# ── Razze (specchio di round160_seed_races.py: slug → gruppo lore) ───────
RACES: dict[str, str] = {
    "human": "umano", "high_elf": "elfico", "wood_elf": "elfico",
    "half_elf": "elfico", "dwarf_mountain": "nanico", "dwarf_hill": "nanico",
    "halfling_lightfoot": "halfling", "halfling_stout": "halfling",
    "gnome_forest": "feerico", "gnome_rock": "nanico", "half_orc": "orco",
    "orc": "orco", "goblin": "selvaggio", "hobgoblin": "selvaggio",
    "kobold": "draconico", "lizardfolk": "rettiloide", "tabaxi": "ferino",
    "tortle": "ferino", "dragonborn_red": "draconico",
    "dragonborn_silver": "draconico", "dragonborn_green": "draconico",
    "tiefling": "infernale", "aasimar": "celestiale",
    "genasi_fire": "elementale", "genasi_water": "elementale",
    "genasi_earth": "elementale", "genasi_air": "elementale",
    "firbolg": "feerico", "centaur": "primordiale", "minotaur": "primordiale",
    "goliath": "gigante", "warforged": "costrutto",
    "changeling": "feerico", "shifter": "ferino", "kalashtar": "psionico",
    "tabaxi_jaguar": "ferino", "yuan_ti": "rettiloide", "fairy": "feerico",
    "satyr": "feerico", "harengon": "feerico", "owlin": "feerico",
    "autognome": "costrutto", "shadar_kai": "shadowfell",
    "eladrin_spring": "feerico", "eladrin_autumn": "feerico",
    "githyanki": "astrale", "githzerai": "astrale", "revenant": "non_morto",
    "dhampir": "non_morto", "cycle_heir": "primordiale",
}

# Palette per gruppo lore: (colore base pelle/figura, accento).
GROUP_COLORS: dict[str, tuple[str, str]] = {
    "umano": ("#c9a27d", "#e0b843"),
    "elfico": ("#d8c9a3", "#7dd87f"),
    "nanico": ("#c98d5f", "#d96f32"),
    "halfling": ("#d9b08c", "#a3d977"),
    "feerico": ("#cdb4de", "#c77dff"),
    "orco": ("#8fae6b", "#4f772d"),
    "selvaggio": ("#a9b46a", "#9c6644"),
    "draconico": ("#c96f6f", "#e63946"),
    "rettiloide": ("#7fae8e", "#2d6a4f"),
    "ferino": ("#d9a066", "#ffb703"),
    "infernale": ("#b56576", "#e5383b"),
    "celestiale": ("#ffe8b6", "#ffd166"),
    "elementale": ("#8ecae6", "#219ebc"),
    "primordiale": ("#b08968", "#7f5539"),
    "gigante": ("#a5a58d", "#6b705c"),
    "costrutto": ("#adb5bd", "#748cab"),
    "psionico": ("#b8b8ff", "#7161ef"),
    "astrale": ("#9fb8d8", "#48cae4"),
    "non_morto": ("#a3a8b8", "#6f7d8c"),
    "shadowfell": ("#6d6875", "#4a4e69"),
}

# Tratti distintivi (SVG frammenti) per gruppo. Riferimento: testa
# centrata in (128, 104), raggio ~42; spalle sotto y=170.
GROUP_MARKS: dict[str, str] = {
    "elfico": '<path d="M84 96 L64 74 L90 82 Z" fill="{base}"/>'
              '<path d="M172 96 L192 74 L166 82 Z" fill="{base}"/>',
    "nanico": '<path d="M100 138 Q128 190 156 138 L156 120 Q128 150 100 120 Z" fill="{accent}" opacity="0.85"/>',
    "orco": '<path d="M112 136 L106 118 L120 130 Z" fill="#f1faee"/>'
            '<path d="M144 136 L150 118 L136 130 Z" fill="#f1faee"/>',
    "infernale": '<path d="M94 74 Q80 48 92 32 Q98 56 108 66 Z" fill="{accent}"/>'
                 '<path d="M162 74 Q176 48 164 32 Q158 56 148 66 Z" fill="{accent}"/>',
    "draconico": '<path d="M92 72 Q70 60 62 40 Q86 48 102 60 Z" fill="{accent}"/>'
                 '<path d="M164 72 Q186 60 194 40 Q170 48 154 60 Z" fill="{accent}"/>',
    "celestiale": '<ellipse cx="128" cy="48" rx="44" ry="10" fill="none" stroke="{accent}" stroke-width="5" opacity="0.9"/>',
    "costrutto": '<circle cx="110" cy="90" r="4" fill="{accent}"/>'
                 '<circle cx="146" cy="90" r="4" fill="{accent}"/>'
                 '<rect x="124" y="52" width="8" height="16" fill="{accent}"/>',
    "ferino": '<path d="M92 76 L86 46 L114 62 Z" fill="{base}"/>'
              '<path d="M164 76 L170 46 L142 62 Z" fill="{base}"/>',
    "rettiloide": '<path d="M112 62 L120 44 L128 62 L136 44 L144 62 Z" fill="{accent}"/>',
    "feerico": '<path d="M116 58 Q112 40 104 36" stroke="{accent}" stroke-width="3" fill="none"/>'
               '<path d="M140 58 Q144 40 152 36" stroke="{accent}" stroke-width="3" fill="none"/>'
               '<circle cx="104" cy="34" r="4" fill="{accent}"/>'
               '<circle cx="152" cy="34" r="4" fill="{accent}"/>',
    "halfling": '<path d="M96 74 Q104 60 116 66 Q124 54 136 62 Q148 52 158 66" stroke="{accent}" stroke-width="6" fill="none" opacity="0.8"/>',
    "umano": "",
    "elementale": '<circle cx="128" cy="104" r="56" fill="none" stroke="{accent}" stroke-width="3" stroke-dasharray="8 8" opacity="0.8"/>',
    "primordiale": '<path d="M88 84 Q60 76 52 54 Q80 60 100 70 Z" fill="{accent}"/>'
                   '<path d="M168 84 Q196 76 204 54 Q176 60 156 70 Z" fill="{accent}"/>',
    "gigante": '<path d="M92 170 L164 170 L158 186 L98 186 Z" fill="{accent}" opacity="0.5"/>',
    "psionico": '<circle cx="128" cy="80" r="6" fill="{accent}"/>'
                '<circle cx="128" cy="80" r="11" fill="none" stroke="{accent}" stroke-width="2" opacity="0.6"/>',
    "astrale": '<path d="M128 66 L132 76 L142 76 L134 82 L137 92 L128 86 L119 92 L122 82 L114 76 L124 76 Z" fill="{accent}"/>',
    "non_morto": '<circle cx="112" cy="98" r="7" fill="#10121c" opacity="0.85"/>'
                 '<circle cx="144" cy="98" r="7" fill="#10121c" opacity="0.85"/>',
    "shadowfell": '<rect x="60" y="120" width="136" height="80" fill="url(#veil)" opacity="0.55"/>',
    "selvaggio": '<path d="M88 92 L74 86 L88 100 Z" fill="{accent}"/>'
                 '<path d="M168 92 L182 86 L168 100 Z" fill="{accent}"/>',
}


def _hue_shift(slug: str) -> int:
    """Piccola variazione deterministica per differenziare razze dello
    stesso gruppo (rotazione hue -12..+12)."""
    h = int(hashlib.sha256(slug.encode()).hexdigest()[:4], 16)
    return (h % 25) - 12


def _shade(hex_color: str, factor: float) -> str:
    """Schiarisce (factor>1, verso il bianco) o scurisce (factor<1) un
    colore #rrggbb. Usato per luci/ombre coerenti con la palette."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    if factor >= 1.0:
        t = factor - 1.0
        r, g, b = (round(c + (255 - c) * t) for c in (r, g, b))
    else:
        r, g, b = (round(c * factor) for c in (r, g, b))
    return f"#{min(r, 255):02x}{min(g, 255):02x}{min(b, 255):02x}"


def avatar_svg(slug: str, gender: str) -> str:
    group = RACES[slug]
    base, accent = GROUP_COLORS[group]
    shift = _hue_shift(slug)
    mark = GROUP_MARKS.get(group, "").format(base=base, accent=accent)
    skin_hi = _shade(base, 1.22)
    skin_dark = _shade(base, 0.72)
    armor = _shade(accent, 0.45)
    armor_hi = _shade(accent, 0.85)
    hair_col = _shade(accent, 0.55)
    if gender == "female":
        # Chioma lunga: massa dietro le spalle + ciocche frontali.
        hair = (
            f'<path d="M80 92 Q70 170 88 204 L106 186 Q92 142 96 98 Z" fill="{hair_col}"/>'
            f'<path d="M176 92 Q186 170 168 204 L150 186 Q164 142 160 98 Z" fill="{hair_col}"/>'
            f'<path d="M84 98 Q84 52 128 50 Q172 52 172 98 Q168 66 128 64 Q88 66 84 98 Z" fill="{hair_col}"/>'
        )
        shoulders = '<path d="M78 212 Q128 160 178 212 L178 256 L78 256 Z"'
        trim = (f'<path d="M82 216 Q128 168 174 216" fill="none" stroke="{armor_hi}" '
                f'stroke-width="4" opacity="0.9"/>')
    else:
        # Taglio corto: calotta aderente.
        hair = (f'<path d="M86 96 Q88 54 128 52 Q168 54 170 96 Q166 72 128 70 '
                f'Q90 72 86 96 Z" fill="{hair_col}"/>')
        shoulders = '<path d="M64 208 Q128 154 192 208 L192 256 L64 256 Z"'
        trim = (f'<path d="M70 212 Q128 162 186 212" fill="none" stroke="{armor_hi}" '
                f'stroke-width="4" opacity="0.9"/>')
    # Volto: occhi + sopracciglia + bocca (i marks di gruppo possono
    # sovrapporsi: es. le occhiaie dei non-morti coprono gli occhi).
    face = (
        f'<ellipse cx="112" cy="102" rx="6" ry="4.5" fill="#10121c"/>'
        f'<ellipse cx="144" cy="102" rx="6" ry="4.5" fill="#10121c"/>'
        f'<circle cx="114" cy="100" r="1.6" fill="#e8ecf4" opacity="0.85"/>'
        f'<circle cx="146" cy="100" r="1.6" fill="#e8ecf4" opacity="0.85"/>'
        f'<path d="M104 92 Q112 88 120 92" stroke="{skin_dark}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="M136 92 Q144 88 152 92" stroke="{skin_dark}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="M119 124 Q128 129 137 124" stroke="{skin_dark}" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.8"/>'
    )
    ring = accent if gender == "female" else base
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{slug} {gender}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="38%" r="75%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.30"/>
      <stop offset="55%" stop-color="#151827"/>
      <stop offset="100%" stop-color="#0b0d16"/>
    </radialGradient>
    <radialGradient id="hd" cx="42%" cy="32%" r="85%">
      <stop offset="0%" stop-color="{skin_hi}"/>
      <stop offset="62%" stop-color="{base}"/>
      <stop offset="100%" stop-color="{skin_dark}"/>
    </radialGradient>
    <linearGradient id="arm" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{armor_hi}"/>
      <stop offset="35%" stop-color="{armor}"/>
      <stop offset="100%" stop-color="#10121c"/>
    </linearGradient>
    <linearGradient id="veil" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0b0d16" stop-opacity="0"/>
      <stop offset="100%" stop-color="#0b0d16"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" fill="url(#bg)"/>
  <g style="filter: hue-rotate({shift}deg)">
    {hair}
    <rect x="114" y="134" width="28" height="34" fill="{skin_dark}"/>
    {shoulders} fill="url(#arm)"/>
    {trim}
    <path d="M120 226 L128 214 L136 226 L128 240 Z" fill="{armor_hi}" opacity="0.9"/>
    <circle cx="128" cy="104" r="42" fill="url(#hd)"/>
    {face}
    {mark}
  </g>
  <rect x="0" y="212" width="256" height="44" fill="url(#veil)" opacity="0.35"/>
  <circle cx="128" cy="128" r="121" fill="none" stroke="{ring}" stroke-width="5" opacity="0.55"/>
  <circle cx="128" cy="128" r="113" fill="none" stroke="{accent}" stroke-width="1.5" stroke-dasharray="3 9" opacity="0.4"/>
</svg>
'''


# ── Banner temi dungeon / raid / sezioni ─────────────────────────────────
# theme → (colore cielo, colore terra, accento, glifo SVG centrale)
GLYPHS: dict[str, str] = {
    "sword": '<path d="M400 70 L414 160 L400 240 L386 160 Z" fill="{a}"/><rect x="368" y="150" width="64" height="12" rx="4" fill="{a}"/><rect x="393" y="162" width="14" height="34" rx="4" fill="{a}"/>',
    "paw": '<circle cx="400" cy="170" r="34" fill="{a}"/><circle cx="360" cy="128" r="15" fill="{a}"/><circle cx="392" cy="112" r="15" fill="{a}"/><circle cx="424" cy="116" r="15" fill="{a}"/><circle cx="448" cy="140" r="14" fill="{a}"/>',
    "tree": '<rect x="392" y="160" width="16" height="70" fill="{a}"/><path d="M400 60 L444 140 L416 134 L448 190 L352 190 L384 134 L356 140 Z" fill="{a}"/>',
    "skull": '<circle cx="400" cy="140" r="52" fill="{a}"/><rect x="374" y="168" width="52" height="40" rx="10" fill="{a}"/><circle cx="382" cy="136" r="12" fill="#0b0d16"/><circle cx="418" cy="136" r="12" fill="#0b0d16"/><rect x="386" y="180" width="7" height="20" fill="#0b0d16"/><rect x="398" y="180" width="7" height="20" fill="#0b0d16"/><rect x="410" y="180" width="7" height="20" fill="#0b0d16"/>',
    "pickaxe": '<rect x="394" y="90" width="12" height="140" rx="4" fill="{a}"/><path d="M320 120 Q400 60 480 120 Q412 96 400 100 Q388 96 320 120 Z" fill="{a}"/>',
    "book": '<path d="M330 110 Q400 90 400 110 L400 210 Q400 190 330 208 Z" fill="{a}"/><path d="M470 110 Q400 90 400 110 L400 210 Q400 190 470 208 Z" fill="{a}" opacity="0.8"/>',
    "snow": '<g stroke="{a}" stroke-width="10" stroke-linecap="round"><line x1="400" y1="80" x2="400" y2="220"/><line x1="340" y1="115" x2="460" y2="185"/><line x1="340" y1="185" x2="460" y2="115"/><line x1="400" y1="80" x2="380" y2="102"/><line x1="400" y1="80" x2="420" y2="102"/><line x1="400" y1="220" x2="380" y2="198"/><line x1="400" y1="220" x2="420" y2="198"/></g>',
    "reed": '<g stroke="{a}" stroke-width="9" stroke-linecap="round" fill="none"><path d="M370 230 Q366 150 380 100"/><path d="M400 230 Q400 140 394 90"/><path d="M430 230 Q436 150 424 104"/></g><ellipse cx="380" cy="94" rx="9" ry="22" fill="{a}"/><ellipse cx="394" cy="82" rx="9" ry="22" fill="{a}"/><ellipse cx="424" cy="96" rx="9" ry="22" fill="{a}"/>',
    "anvil": '<path d="M330 130 L470 130 L470 152 Q430 168 414 168 L414 190 L446 210 L354 210 L386 190 L386 168 Q346 164 330 148 Z" fill="{a}"/>',
    "ship": '<path d="M330 190 L470 190 L440 226 L360 226 Z" fill="{a}"/><rect x="396" y="90" width="8" height="100" fill="{a}"/><path d="M404 96 L462 150 L404 150 Z" fill="{a}" opacity="0.85"/>',
    "arch": '<path d="M340 230 L340 140 Q400 80 460 140 L460 230 L428 230 L428 152 Q400 118 372 152 L372 230 Z" fill="{a}"/>',
    "gear": '<circle cx="400" cy="150" r="52" fill="none" stroke="{a}" stroke-width="22"/><g fill="{a}"><rect x="390" y="70" width="20" height="26"/><rect x="390" y="204" width="20" height="26"/><rect x="316" y="140" width="26" height="20"/><rect x="458" y="140" width="26" height="20"/><rect x="336" y="92" width="22" height="22" transform="rotate(45 347 103)"/><rect x="442" y="92" width="22" height="22" transform="rotate(45 453 103)"/><rect x="336" y="186" width="22" height="22" transform="rotate(45 347 197)"/><rect x="442" y="186" width="22" height="22" transform="rotate(45 453 197)"/></g>',
    "bolt": '<path d="M420 60 L350 170 L392 170 L372 240 L452 130 L408 130 Z" fill="{a}"/>',
    "dragon": '<path d="M330 190 Q350 120 420 110 Q470 106 476 70 Q490 110 452 132 Q480 140 470 170 Q440 150 420 152 Q390 156 380 190 Z" fill="{a}"/><circle cx="452" cy="98" r="6" fill="#0b0d16"/>',
    "void": '<g fill="none" stroke="{a}" stroke-linecap="round"><path d="M400 150 m-60 0 a60 60 0 1 1 120 0" stroke-width="12" opacity="0.5"/><path d="M400 150 m-38 0 a38 38 0 1 0 76 0" stroke-width="10" opacity="0.75"/><path d="M400 150 m-16 0 a16 16 0 1 1 32 0" stroke-width="9"/></g>',
    "flame": '<path d="M400 62 Q436 110 424 150 Q452 138 456 112 Q478 168 440 210 Q414 236 380 224 Q336 206 346 152 Q352 120 376 100 Q368 132 388 142 Q378 96 400 62 Z" fill="{a}"/>',
    "sun": '<circle cx="400" cy="150" r="42" fill="{a}"/><g stroke="{a}" stroke-width="10" stroke-linecap="round"><line x1="400" y1="70" x2="400" y2="92"/><line x1="400" y1="208" x2="400" y2="230"/><line x1="320" y1="150" x2="342" y2="150"/><line x1="458" y1="150" x2="480" y2="150"/><line x1="344" y1="94" x2="360" y2="110"/><line x1="440" y1="190" x2="456" y2="206"/><line x1="344" y1="206" x2="360" y2="190"/><line x1="440" y1="110" x2="456" y2="94"/></g>',
    "worldtree": '<rect x="390" y="150" width="20" height="80" fill="{a}"/><path d="M400 54 Q470 84 466 150 Q430 128 410 138 Q448 160 430 190 Q408 168 400 168 Q392 168 370 190 Q352 160 390 138 Q370 128 334 150 Q330 84 400 54 Z" fill="{a}"/><path d="M380 230 Q360 244 340 240 M420 230 Q440 244 460 240" stroke="{a}" stroke-width="8" fill="none"/>',
    "moon": '<path d="M430 70 A70 70 0 1 0 430 230 A56 56 0 1 1 430 70 Z" fill="{a}"/>',
    "castle": '<path d="M330 230 L330 120 L354 120 L354 100 L374 100 L374 120 L392 120 L392 100 L412 100 L412 120 L430 120 L430 100 L450 100 L450 120 L470 120 L470 230 Z" fill="{a}"/><rect x="388" y="170" width="24" height="60" fill="#0b0d16"/>',
    "bell": '<path d="M400 80 Q440 84 444 150 Q446 180 462 194 L338 194 Q354 180 356 150 Q360 84 400 80 Z" fill="{a}"/><circle cx="400" cy="208" r="12" fill="{a}"/>',
    "chest": '<rect x="330" y="130" width="140" height="90" rx="10" fill="{a}"/><path d="M330 150 Q400 96 470 150 Z" fill="{a}"/><rect x="390" y="150" width="20" height="30" rx="4" fill="#0b0d16"/>',
    "helm": '<path d="M348 200 L348 140 Q348 84 400 84 Q452 84 452 140 L452 200 L424 200 L424 150 L376 150 L376 200 Z" fill="{a}"/><path d="M394 84 L406 84 L406 44 L394 52 Z" fill="{a}"/>',
    "banner_flag": '<path d="M340 80 L460 80 L460 210 L400 176 L340 210 Z" fill="{a}"/>',
    "potion": '<path d="M388 84 L412 84 L412 120 Q448 142 448 180 A48 48 0 0 1 352 180 Q352 142 388 120 Z" fill="{a}"/><rect x="384" y="72" width="32" height="12" rx="4" fill="{a}"/>',
}

THEMES: dict[str, tuple[str, str, str, str]] = {
    # theme: (cielo, terra, accento, glifo)
    "tutorial": ("#1d2233", "#141824", "#e0b843", "sword"),
    "caves": ("#20242f", "#12151d", "#9c6644", "sword"),
    "beast": ("#232a20", "#141a12", "#b08968", "paw"),
    "nature": ("#1c2b1e", "#101a12", "#74c69d", "tree"),
    "crypt": ("#232030", "#131019", "#9d8cd6", "skull"),
    "mines": ("#2b2320", "#181210", "#d96f32", "pickaxe"),
    "library": ("#20283a", "#121724", "#48cae4", "book"),
    "frost": ("#1e2c3a", "#101a24", "#90e0ef", "snow"),
    "marsh": ("#232e26", "#121a14", "#8fae6b", "reed"),
    "forge": ("#2e2119", "#1a110c", "#ff8800", "anvil"),
    "sea": ("#1a2a3d", "#0e1826", "#5aa9e6", "ship"),
    "arena": ("#2b2026", "#171015", "#e5383b", "arch"),
    "clockwork": ("#2a2620", "#171410", "#d4a373", "gear"),
    "storm": ("#242b3d", "#131826", "#ffd166", "bolt"),
    "dragon": ("#301f22", "#1c1012", "#e63946", "dragon"),
    "void": ("#221d33", "#120e1e", "#c77dff", "void"),
    "infernal": ("#331d1a", "#1e0f0c", "#ff4d4d", "flame"),
    "celestial": ("#2b2a3d", "#161526", "#ffd166", "sun"),
    "worldtree": ("#20301f", "#121c11", "#95d5b2", "worldtree"),
    "default": ("#1d2233", "#12151f", "#e0b843", "sword"),
}

RAID_THEMES: dict[str, tuple[str, str, str, str]] = {
    "moonfall-vigil": ("#232a44", "#12172b", "#cfe1ff", "moon"),
    "broken-bastion-siege": ("#2e2622", "#181210", "#e0b843", "castle"),
    "necropolis-bells": ("#25202f", "#120f1a", "#9d8cd6", "bell"),
    "dragon-vault": ("#301f22", "#190f11", "#e63946", "dragon"),
}

SECTION_THEMES: dict[str, tuple[str, str, str, str]] = {
    "dashboard": ("#232438", "#131422", "#e0b843", "banner_flag"),
    "dungeons": ("#20242f", "#12151d", "#e0b843", "arch"),
    "raids": ("#2b2026", "#171015", "#e5383b", "helm"),
    "crafting": ("#2e2119", "#1a110c", "#ff8800", "anvil"),
    "inventory": ("#26221d", "#151310", "#d4a373", "chest"),
    "adventurers": ("#1f2733", "#111721", "#5aa9e6", "helm"),
    "alchemy": ("#221d33", "#120e1e", "#c77dff", "potion"),
}


def _stars(label: str, accent: str) -> str:
    """Campo stellare deterministico (dal label) nella fascia alta."""
    h = hashlib.sha256(label.encode()).digest()
    out = []
    for i in range(24):
        x = 16 + (h[i % 32] * 3 + i * 41) % 768
        y = 10 + (h[(i * 7 + 3) % 32] + i * 11) % 148
        r = (1.0, 1.4, 1.9)[h[(i * 5 + 1) % 32] % 3]
        op = 0.20 + (h[(i * 11 + 5) % 32] % 45) / 100
        fill = accent if i % 3 == 0 else "#dfe6f4"
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" opacity="{op:.2f}"/>')
    return "".join(out)


def banner_svg(sky: str, ground: str, accent: str, glyph_key: str,
               label: str) -> str:
    glyph = GLYPHS[glyph_key].replace("{a}", accent)
    far = _shade(ground, 1.55)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{sky}"/>
      <stop offset="100%" stop-color="{ground}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="46%" r="42%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="vig" x1="0" y1="0" x2="0" y2="1">
      <stop offset="55%" stop-color="#0b0d16" stop-opacity="0"/>
      <stop offset="100%" stop-color="#0b0d16" stop-opacity="0.9"/>
    </linearGradient>
    <filter id="softglow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="800" height="320" fill="url(#sky)"/>
  {_stars(label, accent)}
  <path d="M0 232 L90 176 L170 214 L280 158 L390 210 L500 160 L610 206 L710 168 L800 204 L800 320 L0 320 Z" fill="{far}" opacity="0.5"/>
  <path d="M0 250 L120 190 L210 240 L330 170 L470 240 L580 180 L690 236 L800 200 L800 320 L0 320 Z" fill="{ground}" opacity="0.9"/>
  <path d="M0 280 L160 236 L320 276 L520 230 L680 272 L800 244 L800 320 L0 320 Z" fill="#0b0d16" opacity="0.75"/>
  <rect width="800" height="320" fill="url(#glow)"/>
  <circle cx="400" cy="150" r="104" fill="none" stroke="{accent}" stroke-width="2" opacity="0.35"/>
  <circle cx="400" cy="150" r="120" fill="none" stroke="{accent}" stroke-width="1" stroke-dasharray="4 10" opacity="0.3"/>
  <g filter="url(#softglow)">{glyph}</g>
  <rect width="800" height="320" fill="url(#vig)"/>
  <rect x="8" y="8" width="784" height="304" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.35"/>
  <g stroke="{accent}" stroke-width="3" opacity="0.6" fill="none">
    <path d="M8 34 L8 8 L34 8"/><path d="M766 8 L792 8 L792 34"/>
    <path d="M792 286 L792 312 L766 312"/><path d="M34 312 L8 312 L8 286"/>
  </g>
</svg>
'''


def main() -> None:
    counts = {"avatars": 0, "themes": 0, "raids": 0, "banners": 0}

    av_dir = ASSETS / "avatars"
    av_dir.mkdir(parents=True, exist_ok=True)
    for slug in RACES:
        for gender in ("male", "female"):
            (av_dir / f"{slug}_{gender}.svg").write_text(
                avatar_svg(slug, gender), encoding="utf-8")
            counts["avatars"] += 1
    # Fallback neutro (silhouette umana maschile con ring neutro).
    (av_dir / "default.svg").write_text(
        avatar_svg("human", "male"), encoding="utf-8")

    th_dir = ASSETS / "themes"
    th_dir.mkdir(parents=True, exist_ok=True)
    for theme, (sky, ground, accent, glyph) in THEMES.items():
        (th_dir / f"{theme}.svg").write_text(
            banner_svg(sky, ground, accent, glyph, f"tema {theme}"),
            encoding="utf-8")
        counts["themes"] += 1

    raid_dir = ASSETS / "raids"
    raid_dir.mkdir(parents=True, exist_ok=True)
    for slug, (sky, ground, accent, glyph) in RAID_THEMES.items():
        (raid_dir / f"{slug}.svg").write_text(
            banner_svg(sky, ground, accent, glyph, f"raid {slug}"),
            encoding="utf-8")
        counts["raids"] += 1

    bn_dir = ASSETS / "banners"
    bn_dir.mkdir(parents=True, exist_ok=True)
    for section, (sky, ground, accent, glyph) in SECTION_THEMES.items():
        (bn_dir / f"{section}.svg").write_text(
            banner_svg(sky, ground, accent, glyph, f"sezione {section}"),
            encoding="utf-8")
        counts["banners"] += 1

    print(f"[fase4_genera_assets] generati: {counts} in {ASSETS}")


if __name__ == "__main__":
    main()
