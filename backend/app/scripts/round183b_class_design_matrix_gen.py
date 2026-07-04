"""ROUND 18.3b — Class Design Decision Matrix generator (audit-only).

Legge:
  - `/app/memory/round180b_27_class_canon_raw_data.json` (dati estratti R18.0b)
  - `/app/memory/source_materials/r18_27_class_sources/` (62 file sorgente PM)

Scrive:
  - `/app/memory/round183b_class_design_decision_matrix.md`
  - `/app/memory/round183b_class_design_decision_matrix.json`

ZERO DB write. ZERO scrittura fuori da `/app/memory/round183b_*`.
Zero decisione sigillata: tutto candidato/opzionale, PM decide.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


R18_0B_JSON = Path("/app/memory/round180b_27_class_canon_raw_data.json")
OUT_MD = Path("/app/memory/round183b_class_design_decision_matrix.md")
OUT_JSON = Path("/app/memory/round183b_class_design_decision_matrix.json")

# Bridge item counts (da R18.3a runtime — hardcoded pinned):
BRIDGE_COUNTS = {
    "paladino": 92,        # priest→paladin merge (paladin canonical target)
    "guerriero": 69,       # berserker→warrior alias
    "ladro": 31,           # assassin→rogue alias (0 adv migrated)
    "cacciatore_di_mostri": 31,  # ranger→cacciatore_di_mostri (post R18.3a bridge)
    "cacciatore_del_vuoto": 18,  # warlock→cacciatore_del_vuoto (post R18.3a bridge)
}

# Slug PM-sigillati (Q6): override delle forme brevi estratte da R18.0b
SLUG_OVERRIDES = {
    "cacciatore_mostri": "cacciatore_di_mostri",
    "cacciatore_vuoto": "cacciatore_del_vuoto",
    "cacciatore_sangue": "cacciatore_del_sangue",  # inferred consistent naming
    "cavaliere_morte": "cavaliere_della_morte",
    "cavaliere_draghi": "cavaliere_dei_draghi",
    "giocatore_azzardo": "giocatore_dazzardo",
}

# Stat model proposto (PRELIMINARE — PM può ridefinire):
# Derivato da: descrizione dado vita (d6→magic caster INT/WIS, d10→martial STR/CON),
# risorsa classe, ruoli preliminari, e archetipo fantasy dai file PM.
# NOTA: proposta di lettura, non decisione. PM deve validare per ogni entry.
STAT_MODEL_CANDIDATE = {
    "alchimista":            {"primary_A": "INT",  "primary_B": "DEX", "secondary": ["WIS", "CON"], "rationale": "d6 caster + carica risorsa → INT primary; DEX per bombe/pozioni physical"},
    "artificiere":           {"primary_A": "INT",  "primary_B": "DEX", "secondary": ["CON"],         "rationale": "d6 tinker + carica/runa → INT ; costruzione fisica → DEX"},
    "astrologo":             {"primary_A": "WIS",  "primary_B": "INT", "secondary": ["CHA"],         "rationale": "d8 divinazione + carte/sangue → WIS insight ; INT lettura arcana"},
    "bardo":                 {"primary_A": "CHA",  "primary_B": "INT", "secondary": ["DEX"],         "rationale": "d6 support/control + vuoto/spiriti → CHA performance ; INT sapienza"},
    "burattinaio":           {"primary_A": "INT",  "primary_B": "CHA", "secondary": ["DEX"],         "rationale": "d8 summoner + dominio/vuoto → INT controllo ; CHA imposizione volontà"},
    "cacciatore_del_sangue": {"primary_A": "STR",  "primary_B": "DEX", "secondary": ["CON"],         "rationale": "d8 DPS + furia/sangue → STR raw damage ; DEX weapon versatility"},
    "cacciatore_del_vuoto":  {"primary_A": "INT",  "primary_B": "CHA", "secondary": ["DEX", "WIS"],  "rationale": "d8 DPS/Control + mana/vuoto → INT arcana ; CHA void bond (warlock lineage)"},
    "cacciatore_di_mostri":  {"primary_A": "DEX",  "primary_B": "WIS", "secondary": ["STR", "INT"],  "rationale": "d10 DPS/Utility + essenza/carica/carte → DEX ranger lineage ; WIS hunt lore"},
    "cartografo":            {"primary_A": "INT",  "primary_B": "WIS", "secondary": ["CHA"],         "rationale": "d8 utility + carica/dominio → INT mapping ; WIS pathfinding"},
    "cavaliere_della_morte": {"primary_A": "STR",  "primary_B": "CON", "secondary": ["INT"],         "rationale": "d10 Tank/DPS + mana/furia/essenza → STR martial ; CON undead resilience"},
    "cavaliere_dei_draghi":  {"primary_A": "STR",  "primary_B": "CHA", "secondary": ["CON"],         "rationale": "d10 Tank/DPS + mana/furia/dominio → STR mounted combat ; CHA dragon bond"},
    "cronista":              {"primary_A": "INT",  "primary_B": "CHA", "secondary": ["WIS"],         "rationale": "d6 utility + carica/carte/sangue → INT knowledge ; CHA storytelling"},
    "druido":                {"primary_A": "WIS",  "primary_B": "CON", "secondary": ["STR"],         "rationale": "d6 healer/hybrid + mana/vuoto/spiriti → WIS nature attunement"},
    "fabbro_arcano":         {"primary_A": "INT",  "primary_B": "STR", "secondary": ["CON"],         "rationale": "d8 support/utility + carica/rune → INT craft-lore ; STR forge labor"},
    "giocatore_dazzardo":    {"primary_A": "CHA",  "primary_B": "DEX", "secondary": ["INT"],         "rationale": "d8 hybrid + carica/carte/sangue → CHA luck-charm ; DEX sleight"},
    "guerriero":             {"primary_A": "STR",  "primary_B": "CON", "secondary": ["DEX"],         "rationale": "d10 Tank/DPS + mana/furia/carica → STR classic martial primary"},
    "ladro":                 {"primary_A": "DEX",  "primary_B": "INT", "secondary": ["CHA"],         "rationale": "d8 DPS/Utility + carica/vuoto/rune → DEX classic rogue primary"},
    "mago":                  {"primary_A": "INT",  "primary_B": "WIS", "secondary": ["CON"],         "rationale": "d6 DPS/Control + furia/carica/dominio → INT classic arcane primary"},
    "mercante":              {"primary_A": "CHA",  "primary_B": "INT", "secondary": ["WIS"],         "rationale": "d8 utility/support + carica/sangue/vuoto → CHA trade ; INT economics"},
    "monaco":                {"primary_A": "DEX",  "primary_B": "WIS", "secondary": ["STR"],         "rationale": "d8 DPS/Hybrid + furia/ki/essenza → DEX martial arts ; WIS ki mastery"},
    "negromante":            {"primary_A": "INT",  "primary_B": "WIS", "secondary": ["CON"],         "rationale": "d8 Summoner/DPS + essenza/dominio → INT arcana ; WIS death lore"},
    "paladino":              {"primary_A": "STR",  "primary_B": "CHA", "secondary": ["CON", "WIS"],  "rationale": "d10 Tank/Healer + mana/furia/essenza → STR martial ; CHA divine channeling (priest lineage)"},
    "parassita":             {"primary_A": "CON",  "primary_B": "INT", "secondary": ["STR"],         "rationale": "d8 DPS/Control + mana/carica/dominio → CON biomass host ; INT infestation control"},
    "pittore":               {"primary_A": "CHA",  "primary_B": "INT", "secondary": ["WIS"],         "rationale": "d6 support/control + essenza/carica/sangue → CHA soul expression ; INT pigment arcana"},
    "runista":               {"primary_A": "INT",  "primary_B": "WIS", "secondary": ["CON"],         "rationale": "d6 support/DPS + mana/essenza/carica → INT rune-craft ; WIS ancient script"},
    "sciamano":              {"primary_A": "WIS",  "primary_B": "CHA", "secondary": ["CON"],         "rationale": "d6 healer/support + mana/furia/essenza → WIS spirit ; CHA totem-charm"},
    "sognatore":             {"primary_A": "WIS",  "primary_B": "CHA", "secondary": ["INT"],         "rationale": "d6 control/support + carica/dominio/sangue → WIS oneiric ; CHA dream-manipulation"},
}

# Armor tier candidato (PRELIMINARE — parse manuale dai file R18.0b):
# H=Pesante, M=Media, L=Leggera, N=Nessuna, TBD=OCR sporco
ARMOR_CANDIDATE = {
    "alchimista":            {"tier": "L", "scudi": "TBD", "note": "Base PDF menziona 'armature leggere' preliminare"},
    "artificiere":           {"tier": "M", "scudi": "TBD", "note": "Costruzioni robotiche → medium armor plausible; TBD OCR"},
    "astrologo":             {"tier": "L", "scudi": "N",   "note": "Caster + carte → leggera consistent"},
    "bardo":                 {"tier": "L", "scudi": "N",   "note": "Legacy bard armor leggera"},
    "burattinaio":           {"tier": "L", "scudi": "N",   "note": "Summoner tende leggera; TBD conferma OCR"},
    "cacciatore_del_sangue": {"tier": "M", "scudi": "N",   "note": "Hunter tende media; furia/sangue melee → medium"},
    "cacciatore_del_vuoto":  {"tier": "L", "scudi": "N",   "note": "Warlock lineage → leggera consistente"},
    "cacciatore_di_mostri":  {"tier": "M", "scudi": "N",   "note": "Ranger lineage → media consistent; d10 supporta"},
    "cartografo":            {"tier": "L", "scudi": "N",   "note": "Utility explorer → leggera"},
    "cavaliere_della_morte": {"tier": "H", "scudi": "Sì",  "note": "Death knight canonico H+shield"},
    "cavaliere_dei_draghi":  {"tier": "H", "scudi": "Sì",  "note": "Dragon knight mounted H+shield"},
    "cronista":              {"tier": "L", "scudi": "N",   "note": "Scholar → leggera"},
    "druido":                {"tier": "L", "scudi": "N",   "note": "Legacy druid natural armor (leggera + forme animali)"},
    "fabbro_arcano":         {"tier": "M", "scudi": "TBD", "note": "Craft-heavy → media; TBD scudi"},
    "giocatore_dazzardo":    {"tier": "L", "scudi": "N",   "note": "Sleight-based → leggera"},
    "guerriero":             {"tier": "H", "scudi": "Sì",  "note": "Warrior canonico H+shield"},
    "ladro":                 {"tier": "L", "scudi": "N",   "note": "Rogue canonico leggera"},
    "mago":                  {"tier": "N", "scudi": "N",   "note": "Mage canonico no-armor (o robes → N)"},
    "mercante":              {"tier": "L", "scudi": "N",   "note": "Merchant → leggera"},
    "monaco":                {"tier": "N", "scudi": "N",   "note": "Monk canonico unarmored (ki-based)"},
    "negromante":            {"tier": "L", "scudi": "N",   "note": "Necro classic leggera + robes"},
    "paladino":              {"tier": "H", "scudi": "Sì",  "note": "Paladin canonico H+shield (priest lineage → optional shield)"},
    "parassita":             {"tier": "N", "scudi": "N",   "note": "Biomass host → nessuna (integrata nel corpo)"},
    "pittore":               {"tier": "L", "scudi": "N",   "note": "Artist → leggera"},
    "runista":               {"tier": "M", "scudi": "TBD", "note": "Runecrafter → media plausible; TBD OCR"},
    "sciamano":              {"tier": "L", "scudi": "TBD", "note": "Legacy shaman leggera; scudi tribal TBD"},
    "sognatore":             {"tier": "L", "scudi": "N",   "note": "Dreamweaver → leggera"},
}

# Sovrapposizioni analizzate (§4)
OVERLAPS = [
    {
        "group_id": "OL1",
        "group_name": "Mago vs Runista",
        "classes": ["mago", "runista"],
        "level": "MEDIO",
        "risk": "Mago = arcana pure caster (d6, INT), Runista = arcana rune-craft (d6, INT). Item pool arcana rischia duplicati.",
        "differentiation_options": [
            "Opz A — Mago = damage pure (evocazione/blast), Runista = support/utility (buff/ward via runes)",
            "Opz B — Mago = mana pool tradizionale, Runista = rune-consuming (risorsa dedicata)",
            "Opz C — Mago = single-target, Runista = area/persistent effect (rune inscritte)",
        ],
        "pm_question": "P1-1: Quale differenziazione per Mago vs Runista? (A/B/C/deferred)",
    },
    {
        "group_id": "OL2",
        "group_name": "Guerriero vs Paladino vs Cavaliere della Morte",
        "classes": ["guerriero", "paladino", "cavaliere_della_morte"],
        "level": "ALTO",
        "risk": "3 heavy melee STR-primary d10 armor pesante shield-yes. Rischio party composition ambigua: quale scegliere come Tank principale?",
        "differentiation_options": [
            "Opz A — Guerriero=Tank puro, Paladino=Tank/Healer hybrid, Cavaliere Morte=Tank/DPS con risorsa essenza",
            "Opz B — Distinguere via risorsa: Guerriero=furia, Paladino=mana+essenza divina, CDM=essenza + curse mechanic",
            "Opz C — Distinguere via alignment: Guerriero=neutral, Paladino=light, CDM=dark → tema visivo/narrativo",
        ],
        "pm_question": "P0-3: Differenziazione Guerriero/Paladino/Cavaliere Morte come Tank+DPS d10 STR-heavy (A/B/C)?",
    },
    {
        "group_id": "OL3",
        "group_name": "Cacciatore di Mostri vs Cacciatore del Sangue vs Cacciatore del Vuoto",
        "classes": ["cacciatore_di_mostri", "cacciatore_del_sangue", "cacciatore_del_vuoto"],
        "level": "MEDIO",
        "risk": "3 hunter archetypes. CdM=ranger lineage (DEX, d10, media armor), CdS=blood-magic DPS (STR/DEX, d8, media), CdV=warlock lineage (INT/CHA, d8, leggera). Rischio: item pool 'weapon+hunt gear' condiviso.",
        "differentiation_options": [
            "Opz A — CdM=ranged physical (bow/crossbow, DEX), CdS=melee physical + blood-consume (STR), CdV=arcane ranged + void-consume (INT)",
            "Opz B — CdM=nature/beast focus, CdS=corruption/blood focus, CdV=void/eldritch focus — differenziazione tematica",
            "Opz C — Item pool separati (già in R18.3a: 31 items CdM, 18 items CdV, blood pool TBD)",
        ],
        "pm_question": "P0-4: Differenziazione dei 3 cacciatori come archetype/stat/armor (A/B/C)?",
    },
    {
        "group_id": "OL4",
        "group_name": "Artificiere vs Fabbro Arcano",
        "classes": ["artificiere", "fabbro_arcano"],
        "level": "ALTO",
        "risk": "2 tinker/craft classes con carica risorsa comune. Artificiere=Support/DPS d6 (INT/DEX), Fabbro Arcano=Support/Utility d8 (INT/STR). Rischio item pool 'crafted items' duplicato.",
        "differentiation_options": [
            "Opz A — Artificiere=combat automaton (turrets/robots active), Fabbro Arcano=item enhancement (buff pre-battle)",
            "Opz B — Artificiere=DPS-focused tinker, Fabbro Arcano=pure utility craftsman (0 combat presence, party enabler)",
            "Opz C — Fondere in una singola classe (mossa più drastica: -1 canonical class)",
        ],
        "pm_question": "P1-2: Differenziazione Artificiere vs Fabbro Arcano (A/B/C, C=merge)?",
    },
    {
        "group_id": "OL5",
        "group_name": "Sognatore vs Pittore",
        "classes": ["sognatore", "pittore"],
        "level": "MEDIO",
        "risk": "2 abstract/psy caster d6 CHA/WIS. Sognatore=Control/Support (dream), Pittore=Support/Control (pigmenti-anima). Rischio: player confusion 'chi fa cosa mentale'.",
        "differentiation_options": [
            "Opz A — Sognatore=mental control (charm/sleep/illusion), Pittore=area buff/debuff via 'canvases'",
            "Opz B — Sognatore=INT-based (arcane oneiric), Pittore=CHA-based (art-charisma buff)",
            "Opz C — Merge in singola 'Artista dell'Anima' con 2 rami talenti",
        ],
        "pm_question": "P1-3: Differenziazione Sognatore vs Pittore (A/B/C, C=merge)?",
    },
    {
        "group_id": "OL6",
        "group_name": "Sciamano vs Druido",
        "classes": ["sciamano", "druido"],
        "level": "ALTO",
        "risk": "2 nature/spirit healer. Druido=Healer/Hybrid d6 WIS (già live, druid, 167 adv), Sciamano=Healer/Support d6 WIS/CHA (nuova, 0 adv). Rischio: 167 druid live vs sciamano nuovo → chi ha priorità di feature?",
        "differentiation_options": [
            "Opz A — Druido=nature transformation (forme animali), Sciamano=totem/spirit-bond (evocazione spiriti immateriali)",
            "Opz B — Druido=WIS-primary (nature), Sciamano=CHA-primary (spirit voice)",
            "Opz C — Sciamano diventa specializzazione Druido (2 rami talenti) invece che classe separata",
        ],
        "pm_question": "P1-4: Differenziazione Druido (live 167 adv) vs Sciamano nuovo (A/B/C, C=spec merge)?",
    },
    {
        "group_id": "OL7",
        "group_name": "Mercante vs Giocatore d'Azzardo",
        "classes": ["mercante", "giocatore_dazzardo"],
        "level": "ALTO",
        "risk": "2 economy/luck classes CHA-based d8. Rischio economico: entrambi possono manipolare drop/prezzi/oro → double abuse.",
        "differentiation_options": [
            "Opz A — Mercante=economia strategica (prezzi/inventario), GdA=combat luck/dice/carte (in-fight variance)",
            "Opz B — Mercante=guild-level buff (income+), GdA=party-level buff (single-encounter variance)",
            "Opz C — Bandire una delle due (Mercante o GdA) come classe player e ridurla a NPC",
        ],
        "pm_question": "P1-5: Differenziazione Mercante vs Giocatore d'Azzardo (A/B/C, C=demote NPC)?",
    },
    {
        "group_id": "OL8",
        "group_name": "Cartografo vs Cronista vs Astrologo",
        "classes": ["cartografo", "cronista", "astrologo"],
        "level": "MEDIO",
        "risk": "3 knowledge/utility. Cartografo=Utility/Support d8 (dominio/carica), Cronista=Support/Utility d6 (carte/sangue), Astrologo=Support/Control d8 (carte/sangue). Overlap su 'carte' risorsa.",
        "differentiation_options": [
            "Opz A — Cartografo=exploration (map bonus, world-tier), Cronista=lore/party-XP boost, Astrologo=predictions/buff",
            "Opz B — Distinguere via risorsa unica: Cartografo=dominio, Cronista=sangue, Astrologo=carte (già preliminare)",
            "Opz C — Merge 2 delle 3 (es. Cartografo+Cronista = 'Scholar' con 2 rami)",
        ],
        "pm_question": "P2-1: Differenziazione Cartografo/Cronista/Astrologo (A/B/C, C=merge scholar)?",
    },
]


def _slug_final(slug_candidate: str) -> str:
    """Applica override PM Q6 per slug canonici."""
    return SLUG_OVERRIDES.get(slug_candidate, slug_candidate)


def _extract_class_row(sched: dict, pos: int) -> dict:
    """Costruisce una riga matrice 27 classi da entry R18.0b."""
    raw_slug = sched.get("slug_candidate_non_finale", "")
    slug = _slug_final(raw_slug)
    name = sched.get("class_name_it", "")
    ruoli = sched.get("ruoli_potenziali_preliminari", []) or []
    ruoli_norm = [r.strip() for r in ruoli if r]
    live_cp = sched.get("live_counterpart", "")
    dadi = sched.get("dadi_vita", "TBD")
    risorse = sched.get("risorsa_classe", []) or []
    stat_model = STAT_MODEL_CANDIDATE.get(slug, {})
    armor = ARMOR_CANDIDATE.get(slug, {})

    def has_role(r):
        return r in ruoli_norm

    return {
        "pos": pos,
        "name": name,
        "slug_candidate": slug,
        "slug_pm_override_from_r180b": raw_slug != slug,
        "raw_slug_r180b": raw_slug,
        "archetipo": sched.get("fantasy_archetipo") or "TBD_source_ambiguous",
        "dadi_vita": dadi,
        "risorse_candidate": risorse,
        "roles_possible": {
            "Tank":     has_role("Tank"),
            "Healer":   has_role("Healer"),
            "DPS":      has_role("DPS"),
            "Support":  has_role("Support"),
            "Control":  has_role("Control"),
            "Summoner": has_role("Summoner"),
            "Utility":  has_role("Utility"),
            "Hybrid":   has_role("Hybrid"),
        },
        "stat_primary_A": stat_model.get("primary_A", "TBD"),
        "stat_primary_B": stat_model.get("primary_B", "TBD"),
        "stat_secondary": stat_model.get("secondary", []),
        "stat_rationale": stat_model.get("rationale", "TBD"),
        "armor_tier_candidate": armor.get("tier", "TBD"),
        "shields_candidate": armor.get("scudi", "TBD"),
        "armor_note": armor.get("note", ""),
        "live_counterpart": live_cp,
        "adv_live_count": None,  # will be filled per class if legacy match
        "bridge_item_pool_r18_3a": BRIDGE_COUNTS.get(slug),
        "rischio_tecnico_r180b": sched.get("rischio_tecnico", "?"),
        "dati_mancanti_r180b": sched.get("dati_mancanti_confermati", []) or [],
        "pm_decision_pending_top1": (
            "role (Q7-Q24 deferred)"
            if slug in ("paladino", "guerriero", "ladro", "cacciatore_di_mostri", "cacciatore_del_vuoto")
            else "TBD"
        ),
    }


def _migration_critical_rows(all_rows: list[dict], adv_dist: dict) -> list[dict]:
    critical_slugs = ["paladino", "guerriero", "ladro",
                      "cacciatore_di_mostri", "cacciatore_del_vuoto"]
    legacy_map = {
        "paladino": ("priest → paladin", 190),
        "guerriero": ("berserker → warrior", 3),
        "ladro": ("assassin → rogue", 0),
        "cacciatore_di_mostri": ("ranger → cacciatore_di_mostri", 175),
        "cacciatore_del_vuoto": ("warlock → cacciatore_del_vuoto", 128),
    }
    out = []
    for slug in critical_slugs:
        row = next((r for r in all_rows if r["slug_candidate"] == slug), None)
        if not row:
            continue
        mapping, n_adv = legacy_map[slug]
        role_A = row["stat_primary_A"]
        role_B = row["stat_primary_B"]
        # Roles pri
        r_ok = row["roles_possible"]
        possible_role_A = "Tank" if r_ok["Tank"] else ("DPS" if r_ok["DPS"] else ("Healer" if r_ok["Healer"] else "Support"))
        # secondo ruolo alternativa: se Tank primary, alt = Healer o DPS
        possible_role_B = None
        for r in ["Healer", "DPS", "Support", "Control", "Utility", "Hybrid"]:
            if r != possible_role_A and r_ok.get(r):
                possible_role_B = r
                break
        possible_role_B = possible_role_B or "TBD_PM"

        out.append({
            "slug": slug,
            "name": row["name"],
            "legacy_mapping": mapping,
            "orphans_to_migrate": n_adv,
            "role_option_A": possible_role_A,
            "role_option_B": possible_role_B,
            "stat_primary_A": row["stat_primary_A"],
            "stat_primary_B": row["stat_primary_B"],
            "armor_tier": row["armor_tier_candidate"],
            "shields": row["shields_candidate"],
            "resources_candidate": row["risorse_candidate"],
            "bridge_item_pool": row["bridge_item_pool_r18_3a"],
            "player_facing_migration_risk": (
                f"{n_adv} player vedranno la loro classe cambiare da "
                f"'{mapping.split('→')[0].strip()}' a '{row['name']}' — banner UI IT necessario"
                if n_adv > 0 else "Zero orphan (alias no-migration)"
            ),
            "pm_decision_required": (
                "P0: role finale + stat primary + armor tier "
                f"(opzioni A={possible_role_A}/{row['stat_primary_A']}, "
                f"B={possible_role_B}/{row['stat_primary_B']})"
            ),
        })
    return out


def _pm_questions() -> list[dict]:
    return [
        # P0 — BLOCCANTI per R18.3 apply
        {"id": "P0-1", "priority": "P0", "section": "§2",
         "question": "Ruolo finale Paladino: Tank/Healer hybrid A o Healer/Tank B?",
         "answer_format": "A / B / deferred",
         "blocks": "R18.3 apply (190 priest orphan)"},
        {"id": "P0-2", "priority": "P0", "section": "§2",
         "question": "Ruolo finale Cacciatore di Mostri: DPS puro A o Ranger/Support B?",
         "answer_format": "A / B / deferred",
         "blocks": "R18.3 apply (175 ranger orphan)"},
        {"id": "P0-3", "priority": "P0", "section": "§4 OL2",
         "question": "Differenziazione Guerriero/Paladino/Cavaliere Morte come 3 tank-DPS d10 STR-heavy?",
         "answer_format": "A (ruoli distinti) / B (risorse distinte) / C (alignment) / deferred",
         "blocks": "R18.3 apply + R18.4 item class-bound"},
        {"id": "P0-4", "priority": "P0", "section": "§4 OL3",
         "question": "Differenziazione dei 3 cacciatori (di Mostri / del Sangue / del Vuoto)?",
         "answer_format": "A (physical vs blood vs arcane) / B (tematica) / C (item-pool) / deferred",
         "blocks": "R18.3 apply (303 hunter-ish orphan)"},
        {"id": "P0-5", "priority": "P0", "section": "§2",
         "question": "Ruolo finale Cacciatore del Vuoto: DPS/Caster A o Support/Control B?",
         "answer_format": "A / B / deferred",
         "blocks": "R18.3 apply (128 warlock orphan)"},
        {"id": "P0-6", "priority": "P0", "section": "§5",
         "question": "Stat primaria Paladino: STR (martial) A o CHA (divine channeling) B?",
         "answer_format": "A / B / entrambe (dual-primary) / deferred",
         "blocks": "R18.3 apply + R18.4 armor requirements"},
        {"id": "P0-7", "priority": "P0", "section": "§6",
         "question": "Armor tier finale Cacciatore di Mostri: Media (ranger lineage) o Leggera (agility)?",
         "answer_format": "Media / Leggera / deferred",
         "blocks": "R18.3 apply + R18.4 item catalog"},

        # P1 — BLOCCANTI R18.4 (item class-bound)
        {"id": "P1-1", "priority": "P1", "section": "§4 OL1",
         "question": "Differenziazione Mago vs Runista (arcana caster overlap)?",
         "answer_format": "A / B / C / deferred",
         "blocks": "R18.4 item class-bound (arcana items)"},
        {"id": "P1-2", "priority": "P1", "section": "§4 OL4",
         "question": "Differenziazione Artificiere vs Fabbro Arcano (tinker overlap)?",
         "answer_format": "A / B / C=merge / deferred",
         "blocks": "R18.4 crafting items"},
        {"id": "P1-3", "priority": "P1", "section": "§4 OL5",
         "question": "Differenziazione Sognatore vs Pittore (abstract-psy overlap)?",
         "answer_format": "A / B / C=merge / deferred",
         "blocks": "R18.4 caster items"},
        {"id": "P1-4", "priority": "P1", "section": "§4 OL6",
         "question": "Differenziazione Druido (167 live) vs Sciamano nuovo?",
         "answer_format": "A / B / C=spec merge / deferred",
         "blocks": "R18.4 healer items + potential R18.3 druid impact"},
        {"id": "P1-5", "priority": "P1", "section": "§4 OL7",
         "question": "Differenziazione Mercante vs Giocatore d'Azzardo (economy/luck overlap)?",
         "answer_format": "A / B / C=demote NPC / deferred",
         "blocks": "R18.4 economy items"},
        {"id": "P1-6", "priority": "P1", "section": "§6",
         "question": "Scudi Sì/No per: Alchimista, Artificiere, Fabbro Arcano, Runista, Sciamano (TBD OCR)?",
         "answer_format": "Sì / No / per-classe / deferred",
         "blocks": "R18.4 item slot equipment"},
        {"id": "P1-7", "priority": "P1", "section": "§7",
         "question": "Risorse finali dominio + carica + essenza + vuoto + sangue + carte + spiriti + rune + furia + ki + mana → 11 candidate. Quali sigillare come canoniche (max 6-8 raccomandato)?",
         "answer_format": "elenco slug sigillati / deferred",
         "blocks": "R18.4 combat resource system"},

        # P2 — BLOCCANTI R18.5 (talenti reali)
        {"id": "P2-1", "priority": "P2", "section": "§4 OL8",
         "question": "Differenziazione Cartografo vs Cronista vs Astrologo (knowledge overlap)?",
         "answer_format": "A / B / C=merge scholar / deferred",
         "blocks": "R18.5 talent branch overlap"},
        {"id": "P2-2", "priority": "P2", "section": "§3",
         "question": "3 rami talenti canonici per classe: nomi standard (es. per Paladino 'Vendetta', 'Devozione', 'Protezione')?",
         "answer_format": "per-classe elenco / template comune / deferred",
         "blocks": "R18.5 talent tree naming"},
        {"id": "P2-3", "priority": "P2", "section": "§3",
         "question": "Bonus preliminari 5 tier x 4 talenti per ramo: pattern (es. +Damage / +Utility / +Defensive)?",
         "answer_format": "pattern / per-classe custom / deferred",
         "blocks": "R18.5 talent bonus formula"},

        # P3 — Polish/futuro
        {"id": "P3-1", "priority": "P3", "section": "§3",
         "question": "Achievement dedicati per classi non-live (17/27 senza adv attuali) — priorità high o low?",
         "answer_format": "high / low / per-classe / deferred",
         "blocks": "R18.6+ achievement content"},
        {"id": "P3-2", "priority": "P3", "section": "§3",
         "question": "Set item cross-classe (es. 'Set del Cacciatore' per tutti e 3 i cacciatori) o item pool 100% separati?",
         "answer_format": "cross / separati / deferred",
         "blocks": "R18.7 item expansion"},
        {"id": "P3-3", "priority": "P3", "section": "§5",
         "question": "Naming stat: adottare 6-stat standard (STR/DEX/CON/INT/WIS/CHA) o mantenere schema legacy Orbus (Strength/Agility/Intellect/Endurance/Faith)?",
         "answer_format": "6-stat / legacy 5-stat / mapping / deferred",
         "blocks": "R18.X polish + adventurer_public serializer"},
    ]


def _top_5_risks(rows: list[dict]) -> list[dict]:
    return [
        {"rank": 1, "risk": "Item pool bridge cacciatore_del_vuoto (18 items) insufficiente per 128 adv migrated",
         "mitigation": "R18.4 espandere pool warlock/void items OR abbassare item-slot requirement per migration graduale"},
        {"rank": 2, "risk": "8 sovrapposizioni (Mago/Runista, 3 Tank d10, 3 Hunter, Artificiere/Fabbro, ecc.) generano item pool duplicati",
         "mitigation": "R18.3b PM decisioni P1-1..P1-5 + R18.4 item-pool audit per rimuovere duplicati"},
        {"rank": 3, "risk": "17/27 classi senza live adventurers (0 baseline) → onboarding e recruitment devono creare rappresentazione",
         "mitigation": "R18.3 apply + recruit generator adapt (deferred a decisione P0)"},
        {"rank": 4, "risk": "11 risorse candidate (mana/furia/carica/ki/carte/vuoto/sangue/essenza/dominio/rune/spiriti) → sistema combat troppo eterogeneo",
         "mitigation": "P1-7 sigillare max 6-8 risorse canoniche in R18.5 pre-implementation"},
        {"rank": 5, "risk": "OCR sporco su alcuni PDF (armor_tier + scudi TBD per 5-7 classi)",
         "mitigation": "R18.3b PM P1-6 chiarire scudi via testo diretto anziché tabelle formattate"},
    ]


def _recommendation() -> dict:
    return {
        "priority_order": [
            "P0-1 (Paladino role) — 190 adv più grande gruppo migrato",
            "P0-2 (Cacciatore di Mostri role) — 175 adv",
            "P0-5 (Cacciatore del Vuoto role) — 128 adv",
            "P0-4 (differenziazione 3 hunter) — sblocca item pool R18.4",
            "P0-3 (differenziazione 3 tank) — sblocca item pool R18.4",
            "P0-6 (stat primary Paladino) — decide 190 adv equip",
            "P0-7 (armor CdM) — decide 175 adv equip",
        ],
        "rationale": (
            "Rispondere P0-1 per primo perché blocca R18.3 apply per il gruppo "
            "più numeroso (190 priest → paladin). Poi P0-2 + P0-5 per completare "
            "il quadro dei 493 orphan migrated (fuori i 3 berserker + 0 assassin, "
            "già alias no-brainer). P0-4 + P0-3 poi risolvono item pool conflicts. "
            "P0-6 + P0-7 sono raffinamenti dettagliati."
        ),
    }


def build_output() -> tuple[dict, str]:
    if not R18_0B_JSON.exists():
        print(f"[fatal] {R18_0B_JSON} missing", file=sys.stderr)
        sys.exit(2)
    src = json.loads(R18_0B_JSON.read_text())
    scheds = src.get("schede_27_classi", [])
    adv_dist = src.get("live_adv_distribution", {})

    rows = [_extract_class_row(s, i + 1) for i, s in enumerate(scheds)]
    # Fill adv_live_count from live_counterpart
    for r in rows:
        cp = r.get("live_counterpart")
        if cp and cp != "NO_LIVE_MATCH":
            r["adv_live_count"] = adv_dist.get(cp, 0)

    migration_critical = _migration_critical_rows(rows, adv_dist)
    pm_qs = _pm_questions()

    counts = {
        "n_classes_total": len(rows),
        "n_classes_with_live_counterpart": sum(1 for r in rows if r.get("adv_live_count") is not None),
        "n_classes_without_live": sum(1 for r in rows if r.get("adv_live_count") is None),
        "n_classes_stat_model_filled": sum(1 for r in rows if r["stat_primary_A"] != "TBD"),
        "n_classes_armor_tier_filled": sum(1 for r in rows if r["armor_tier_candidate"] not in ("TBD", "")),
        "n_classes_with_tbd_source_silent_resources": sum(1 for r in rows if not r["risorse_candidate"]),
        "pm_questions_by_priority": {
            "P0": sum(1 for q in pm_qs if q["priority"] == "P0"),
            "P1": sum(1 for q in pm_qs if q["priority"] == "P1"),
            "P2": sum(1 for q in pm_qs if q["priority"] == "P2"),
            "P3": sum(1 for q in pm_qs if q["priority"] == "P3"),
        },
        "overlaps_by_risk": {
            "ALTO": sum(1 for o in OVERLAPS if o["level"] == "ALTO"),
            "MEDIO": sum(1 for o in OVERLAPS if o["level"] == "MEDIO"),
            "BASSO": sum(1 for o in OVERLAPS if o["level"] == "BASSO"),
        },
        "armor_distribution": {
            "H_pesante": sum(1 for r in rows if r["armor_tier_candidate"] == "H"),
            "M_media":   sum(1 for r in rows if r["armor_tier_candidate"] == "M"),
            "L_leggera": sum(1 for r in rows if r["armor_tier_candidate"] == "L"),
            "N_nessuna": sum(1 for r in rows if r["armor_tier_candidate"] == "N"),
            "TBD":       sum(1 for r in rows if r["armor_tier_candidate"] == "TBD"),
        },
        "shields_distribution": {
            "Sì": sum(1 for r in rows if r["shields_candidate"] == "Sì"),
            "N":  sum(1 for r in rows if r["shields_candidate"] == "N"),
            "TBD": sum(1 for r in rows if r["shields_candidate"] == "TBD"),
        },
    }

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "round": "R18.3b",
        "phase": "class_design_decision_matrix (audit-only, decision support)",
        "authority": "PM-facing decision support — ZERO sealed decisions",
        "constraints": [
            "zero DB write", "zero migration", "zero seed",
            "zero UI player-facing", "zero item bridge nuovo",
            "zero talenti reali", "zero auto-equip/combat math modification",
            "all options CANDIDATE — PM decides",
        ],
        "sources": {
            "primary": "round180b_27_class_canon_raw_data.json",
            "raw_pdfs_dir": "source_materials/r18_27_class_sources/",
            "live_db_ref": "adventurer_classes + live_adv_distribution snapshot R18.0b",
        },
        "counts": counts,
        "migration_critical_classes": migration_critical,
        "matrix_27_classes": rows,
        "overlaps_analysis": OVERLAPS,
        "stat_model_candidate": STAT_MODEL_CANDIDATE,
        "armor_shields_candidate": ARMOR_CANDIDATE,
        "pm_questions": pm_qs,
        "top_5_technical_risks": _top_5_risks(rows),
        "recommendation": _recommendation(),
        "adv_live_distribution_snapshot": adv_dist,
    }

    # ─── Build MD report ───
    md_parts: list[str] = []
    md_parts.append(f"# ROUND 18.3b — Class Design Decision Matrix (Audit-only)\n")
    md_parts.append(f"**Round**: R18.3b · **Data**: {output['generated_at_utc']} · **Status**: OPEN — Decision Support\n\n")
    md_parts.append("**Autorità**: PM-facing. Zero decisioni sigillate. Tutte le opzioni sono candidate.\n\n---\n\n")

    # §1
    md_parts.append("## §1 · Executive summary\n\n")
    md_parts.append(
        "Il round R18.3 apply (migration reale 496 orphan) è **DEFERRED** finché "
        "il PM non decide un minimo di **7 domande P0** che riguardano le 5 classi "
        "migration-critical (paladino, guerriero, ladro, cacciatore_di_mostri, "
        "cacciatore_del_vuoto). Post-R18.3a le 2 classi target esistono in catalog "
        "con `role='TBD'` + `role_pm_decision_pending=true` — questo report fornisce "
        "il materiale per rispondere a Q7-Q24.\n\n"
    )
    md_parts.append(f"**Impatto migration futura**: **303 adv** (175 ranger → cacciatore_di_mostri + 128 warlock → cacciatore_del_vuoto) migreranno verso classi con `role='TBD'` e stat non definite. Senza P0 risolti, i 303 adv resterebbero con dati provvisori.\n\n")
    md_parts.append(f"**Conteggi domande PM per priorità**:\n")
    for pri, n in counts["pm_questions_by_priority"].items():
        md_parts.append(f"- **{pri}**: {n} domande\n")
    md_parts.append(f"\n**Ambiguità note su fonti**: OCR sporco su tabelle armor/scudi per 5-7 classi (Alchimista, Artificiere, Fabbro Arcano, Runista, Sciamano). Alcune classi hanno `fantasy_archetipo=TBD_source_readable_but_extraction_regex_missed_quote_marker` — testo leggibile ma citazione non estraibile via regex.\n\n---\n\n")

    # §2 Migration-critical
    md_parts.append("## §2 · Migration-Critical Classes (PRIORITÀ MASSIMA)\n\n")
    md_parts.append("| # | Classe | Slug | Legacy mapping | Orphan | Role A | Role B | Stat prim A | Stat prim B | Armor | Scudi | Bridge pool | Rischio player-facing | Decisione PM |\n")
    md_parts.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for i, mc in enumerate(migration_critical, 1):
        md_parts.append(
            f"| {i} | {mc['name']} | `{mc['slug']}` | {mc['legacy_mapping']} | "
            f"**{mc['orphans_to_migrate']}** | {mc['role_option_A']} | {mc['role_option_B']} | "
            f"{mc['stat_primary_A']} | {mc['stat_primary_B']} | {mc['armor_tier']} | {mc['shields']} | "
            f"{mc['bridge_item_pool']} | {mc['player_facing_migration_risk']} | {mc['pm_decision_required']} |\n"
        )
    md_parts.append("\n---\n\n")

    # §3 27-class matrix
    md_parts.append("## §3 · Matrice completa 27 classi\n\n")
    md_parts.append("Legenda ruoli: T=Tank · H=Healer · D=DPS · S=Support · C=Control · U=Utility · Su=Summoner · Hy=Hybrid\n\n")
    md_parts.append("| # | Nome | Slug | Dadi | T | H | D | S | C | U | Su | Hy | Stat A | Stat B | Armor | Scudi | Risorse | Live adv | Bridge | Rischio |\n")
    md_parts.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    role_keys = [("Tank","T"),("Healer","H"),("DPS","D"),("Support","S"),
                 ("Control","C"),("Utility","U"),("Summoner","Su"),("Hybrid","Hy")]
    for r in rows:
        rf = r["roles_possible"]
        role_flags = " | ".join("✓" if rf[k] else "" for k, _ in role_keys)
        adv = r.get("adv_live_count")
        adv_s = str(adv) if adv is not None else "—"
        bridge = r.get("bridge_item_pool_r18_3a")
        bridge_s = str(bridge) if bridge is not None else "—"
        risorse_s = ", ".join(r["risorse_candidate"][:3]) or "—"
        md_parts.append(
            f"| {r['pos']} | {r['name']} | `{r['slug_candidate']}` | {r['dadi_vita']} | "
            f"{role_flags} | {r['stat_primary_A']} | {r['stat_primary_B']} | "
            f"{r['armor_tier_candidate']} | {r['shields_candidate']} | {risorse_s} | "
            f"{adv_s} | {bridge_s} | {r['rischio_tecnico_r180b']} |\n"
        )
    md_parts.append(f"\n**Note**: `{counts['n_classes_stat_model_filled']}/27` classi con stat model candidato compilato, `{counts['n_classes_armor_tier_filled']}/27` con armor tier candidato, `{counts['n_classes_without_live']}/27` senza live counterpart.\n\n---\n\n")

    # §4 Overlaps
    md_parts.append("## §4 · Sovrapposizioni da risolvere (8 gruppi)\n\n")
    for ol in OVERLAPS:
        md_parts.append(f"### {ol['group_id']} · {ol['group_name']} — livello **{ol['level']}**\n\n")
        md_parts.append(f"- **Classi**: {', '.join('`'+c+'`' for c in ol['classes'])}\n")
        md_parts.append(f"- **Rischio**: {ol['risk']}\n")
        md_parts.append(f"- **Opzioni differenziazione**:\n")
        for opt in ol['differentiation_options']:
            md_parts.append(f"  - {opt}\n")
        md_parts.append(f"- **Decisione PM**: {ol['pm_question']}\n\n")
    md_parts.append("---\n\n")

    # §5 Stat model
    md_parts.append("## §5 · Stat model proposto (PRELIMINARE — PM può ridefinire)\n\n")
    md_parts.append("Uso 6-stat standard (STR/DEX/CON/INT/WIS/CHA). "
                    "Marca esplicitamente ogni entry come **candidato** — nessuna decisione sigillata.\n\n")
    md_parts.append("| Slug | Primary A | Primary B | Secondary | Rationale |\n")
    md_parts.append("|---|---|---|---|---|\n")
    for slug, model in STAT_MODEL_CANDIDATE.items():
        sec = ", ".join(model.get("secondary", []))
        md_parts.append(f"| `{slug}` | **{model['primary_A']}** | {model['primary_B']} | {sec} | {model['rationale']} |\n")
    md_parts.append(f"\n**Coverage**: {counts['n_classes_stat_model_filled']}/27 classi con proposta stat. "
                    "Nessuna decisione applicata al catalog live.\n\n---\n\n")

    # §6 Armor/scudi
    md_parts.append("## §6 · Armor tier + scudi (candidato)\n\n")
    md_parts.append("Legenda: **H**=Pesante · **M**=Media · **L**=Leggera · **N**=Nessuna · **TBD**=OCR sporco\n\n")
    md_parts.append("| Slug | Armor tier | Scudi | Note |\n|---|---|---|---|\n")
    for slug, a in ARMOR_CANDIDATE.items():
        md_parts.append(f"| `{slug}` | **{a['tier']}** | {a['scudi']} | {a['note']} |\n")
    md_parts.append(f"\n**Distribuzione armor**:\n")
    for tier, n in counts["armor_distribution"].items():
        md_parts.append(f"- {tier}: {n} classi\n")
    md_parts.append(f"\n**Distribuzione scudi**:\n")
    for k, n in counts["shields_distribution"].items():
        md_parts.append(f"- {k}: {n} classi\n")
    md_parts.append("\n**Conflitti/ambiguità**: 5 classi con `scudi=TBD` (OCR sporco) — vedi P1-6.\n\n---\n\n")

    # §7 Risorse
    md_parts.append("## §7 · Risorse di classe (estratto dai file sorgente)\n\n")
    # Aggregate resources
    all_resources: dict[str, list[str]] = {}
    for r in rows:
        for res in r["risorse_candidate"]:
            all_resources.setdefault(res, []).append(r["slug_candidate"])
    md_parts.append("| Risorsa | Classi che la usano | N |\n|---|---|---|\n")
    for res, slugs in sorted(all_resources.items(), key=lambda x: -len(x[1])):
        md_parts.append(f"| `{res}` | {', '.join(slugs)} | {len(slugs)} |\n")
    md_parts.append(f"\n**Risorse candidate uniche**: {len(all_resources)} (proposte, PM deve sigillare — vedi P1-7).\n")
    md_parts.append(f"**Classi con `TBD source_silent`** (nessuna risorsa estratta): {counts['n_classes_with_tbd_source_silent_resources']}.\n\n---\n\n")

    # §8 PM questions
    md_parts.append("## §8 · Domande PM finali (ordinate per priorità)\n\n")
    for pri in ["P0", "P1", "P2", "P3"]:
        md_parts.append(f"### {pri} — {counts['pm_questions_by_priority'][pri]} domande\n\n")
        pri_qs = [q for q in pm_qs if q["priority"] == pri]
        for q in pri_qs:
            md_parts.append(f"- **`{q['id']}`** ({q['section']}) — {q['question']}\n")
            md_parts.append(f"  - Risposta: `{q['answer_format']}`\n")
            md_parts.append(f"  - Blocca: {q['blocks']}\n\n")
    md_parts.append("---\n\n")

    # Top 5 risks + recommendation
    md_parts.append("## Rischi tecnici globali (top 5)\n\n")
    for r in _top_5_risks(rows):
        md_parts.append(f"{r['rank']}. **{r['risk']}**\n   - Mitigation: {r['mitigation']}\n\n")
    md_parts.append("---\n\n")

    md_parts.append("## Raccomandazione ordine risposta PM\n\n")
    rec = _recommendation()
    for p in rec["priority_order"]:
        md_parts.append(f"- {p}\n")
    md_parts.append(f"\n**Rationale**: {rec['rationale']}\n\n---\n\n")

    md_parts.append("## Conferma vincoli R18.3b\n\n")
    for c in output["constraints"]:
        md_parts.append(f"- ✅ {c}\n")
    md_parts.append("\n---\n\n")
    md_parts.append("*Firma: e1 main agent · R18.3b OPEN · decision support only.*\n")

    md_text = "".join(md_parts)
    return output, md_text


def main() -> None:
    output, md_text = build_output()
    OUT_MD.write_text(md_text)
    OUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    md_lines = md_text.count("\n") + 1
    n_keys = len(output.keys())
    print(f"[out] MD: {OUT_MD} · {md_lines} righe · {len(md_text)} char")
    print(f"[out] JSON: {OUT_JSON} · {n_keys} chiavi top-level")
    print(f"[counts] P0={output['counts']['pm_questions_by_priority']['P0']} "
          f"P1={output['counts']['pm_questions_by_priority']['P1']} "
          f"P2={output['counts']['pm_questions_by_priority']['P2']} "
          f"P3={output['counts']['pm_questions_by_priority']['P3']}")


if __name__ == "__main__":
    main()
