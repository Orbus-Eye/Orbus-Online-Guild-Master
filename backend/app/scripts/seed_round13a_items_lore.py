"""ROUND 13a — Idempotent lore + level enrichment seed for items.

Adds for every `db.items` row (non-test, non-inactive):
  * `required_adventurer_level` (explicit MAX(rarity_lvl, tier_lvl, raid_lvl))
  * `display_name_it` (override visivo; non sostituisce `name`/`slug`)
  * `display_name_en`
  * `flavor_text_it` (max ~200 char, può essere None per Common neutri)
  * `flavor_text_en`
  * `lore_tags` (array)
  * `lore_source = "orbus_lore_book_v1"`
  * `lore_reviewed = True`, `lore_reviewed_at`
  * `spoiler_level` ∈ {public, mystery, hidden, internal}

Idempotent: re-runs sono no-op se `lore_reviewed=True`. Slug invariati,
`name` invariato (backward compat).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.database import db

logger = logging.getLogger("orbus.seed_round13a_items_lore")

LORE_SOURCE = "orbus_lore_book_v1"

# Rarity → minimum required adventurer level
_RARITY_LVL = {
    "Common": 1, "Uncommon": 3, "Rare": 5,
    "Epic": 8, "Legendary": 12, "Signature": 5,
}
_RARITY_CANONICAL = {
    rarity.casefold(): rarity for rarity in _RARITY_LVL
}

# Slug → manual lore-flavored display name (Italian).
# Per ogni rarità ho preparato un mix di nomi cultural-coherent.
# Common: nomi puliti, no lore heavy.
# Uncommon: riferimenti soft.
# Rare/Epic/Legendary: riferimenti lore espliciti.
COMMON_LORE_OVERRIDES: dict[str, dict[str, Any]] = {
    "acolyte-mace": {
        "it": "Mazza del Primo Rintocco",
        "flavor_it": "Nella cappella bassa suonò una sola volta, quando il novizio decise di restare.",
        "tags": ["cappella-bassa", "novizi"],
    },
    "apprentice-handbook": {
        "it": "Manuale delle Pagine Macchiate",
        "flavor_it": "Le formule incompiute hanno più correzioni che incantesimi, ma nessuna pagina è stata strappata.",
        "tags": ["apprendisti", "archivio"],
    },
    "apprentice-robe": {
        "it": "Veste dell'Inchiostro Incompiuto",
        "flavor_it": "Le macchie sulle maniche seguono la mappa di una costellazione che nessun maestro riconosce.",
        "tags": ["apprendisti", "costellazioni"],
    },
    "apprentice-wand": {
        "it": "Verga dalla Punta di Rame",
        "flavor_it": "Scintilla prima di obbedire, come se ricordasse ancora le mani del suo primo artefice.",
        "tags": ["apprendisti", "rame"],
    },
    "chipped_ring": {
        "it": "Anello della Tacca Ostinata",
        "flavor_it": "La tacca non si allarga da anni, benché ogni proprietario giuri di averla vista muoversi.",
        "tags": ["mercato-basso", "memoria"],
    },
    "conscripts-helm": {
        "it": "Elmo della Quinta Leva",
        "flavor_it": "Sul bordo interno sono incise cinque iniziali; solo quattro compaiono nei registri della guarnigione.",
        "tags": ["guarnigione", "quinta-leva"],
    },
    "copper-ring": {
        "it": "Vera di Rame del Mercato Basso",
        "flavor_it": "I mercanti la usavano come promessa quando una stretta di mano non bastava.",
        "tags": ["mercato-basso", "rame"],
    },
    "cracked-staff": {
        "it": "Bastone della Crepa Sonora",
        "flavor_it": "La frattura vibra vicino alle porte sigillate, sempre un istante prima che cedano.",
        "tags": ["porte-sigillate", "eco"],
    },
    "driftwood-charm": {
        "it": "Talismano del Legno alla Deriva",
        "flavor_it": "Il mare lo restituì tre volte alla stessa spiaggia, ogni volta legato con un nodo diverso.",
        "tags": ["costa", "ritorni"],
    },
    "healing_herb": {
        "it": "Erba del Sollievo Verde",
        "flavor_it": "Cresce dove i guaritori di strada versano l'ultima goccia delle loro fiasche.",
        "tags": ["guaritori", "sentieri"],
    },
    "hempcloth-tunic": {
        "it": "Tunica di Canapa delle Case Basse",
        "flavor_it": "Ruvida e tenace, porta il marchio delle tessitrici che non abbandonarono il quartiere durante l'assedio.",
        "tags": ["case-basse", "assedio"],
    },
    "herbalist-pouch": {
        "it": "Bisaccia delle Sette Radici",
        "flavor_it": "Sei radici curano mali conosciuti; la settima viene conservata per una febbre senza nome.",
        "tags": ["erboristi", "sette-radici"],
    },
    "hunting-knife": {
        "it": "Coltello del Coniglio Grigio",
        "flavor_it": "I cacciatori di Elfwood lo posano a terra quando una preda attraversa il sentiero senza lasciare ombra.",
        "tags": ["elfwood", "cacciatori"],
    },
    "iron_shard": {
        "it": "Scheggia della Prima Forgia",
        "flavor_it": "È fredda finché non viene avvicinata al cancello di Krastlov; allora ricorda il fuoco.",
        "tags": ["krastlov", "forgia"],
    },
    "leather-cap": {
        "it": "Berretto del Conciatore Silenzioso",
        "flavor_it": "Il conciatore non firmava il suo lavoro: lasciava tre punti neri sotto la visiera.",
        "tags": ["conciatori", "case-basse"],
    },
    "light_cuirass": {
        "it": "Corazza Leggera del Passo Rapido",
        "flavor_it": "Fu disegnata per i messaggeri che attraversavano le mura prima che le campane finissero di suonare.",
        "tags": ["messaggeri", "mura"],
    },
    "minor_healing_potion": {
        "it": "Fiala del Primo Sollievo",
        "flavor_it": "La ricetta è semplice; il segreto è lasciare una goccia per chi verrà dopo.",
        "tags": ["guaritori", "fiale"],
    },
    "novice-charm": {
        "it": "Ciondolo della Soglia",
        "flavor_it": "Ogni novizio lo stringe prima di varcare la porta, ma nessuno ricorda di averlo ricevuto.",
        "tags": ["novizi", "soglia"],
    },
    "oak-cudgel": {
        "it": "Randello della Quercia Nodosa",
        "flavor_it": "Tagliato da un ramo caduto senza vento nella notte della prima Veglia.",
        "tags": ["veglie", "quercia"],
    },
    "padded-jerkin": {
        "it": "Farsetto delle Tre Imbottiture",
        "flavor_it": "Tra gli strati è cucita una lettera mai consegnata a un soldato del fronte orientale.",
        "tags": ["fronte-orientale", "lettere"],
    },
    "pitchfork": {
        "it": "Forcone della Mietitura Interrotta",
        "flavor_it": "Rimase conficcato nel campo quando il raccolto si fermò a metà e le ombre continuarono a lavorare.",
        "tags": ["campi", "ombre"],
    },
    "raw_leather": {
        "it": "Cuoio della Caccia d'Autunno",
        "flavor_it": "Conserva l'odore delle foglie bagnate e di una pista che terminava davanti a un albero cavo.",
        "tags": ["elfwood", "caccia"],
    },
    "river-pebble-charm": {
        "it": "Ciondolo del Ciottolo di Irthe",
        "flavor_it": "L'acqua di Irthe lo ha levigato senza cancellare il segno sottile inciso al centro.",
        "tags": ["irthe", "fiume"],
    },
    "road-walkers-staff": {
        "it": "Bastone delle Miglia Incise",
        "flavor_it": "Ogni tacca corrisponde a una strada percorsa; l'ultima indica un luogo che non compare sulle mappe.",
        "tags": ["strade", "cartografi"],
    },
    "rough-flail": {
        "it": "Flagello della Catena Annodata",
        "flavor_it": "Il nodo centrale fu stretto da un fabbro che rifiutava di forgiare armi per i signori della guerra.",
        "tags": ["fabbri", "rivolta"],
    },
    "rusted-sword": {
        "it": "Spada della Ruggine Rossa",
        "flavor_it": "La lama non torna lucida, ma la ruggine forma ogni alba una nuova linea di battaglia.",
        "tags": ["campi-di-battaglia", "memoria"],
    },
    "scout-shortbow": {
        "it": "Arco Corto del Sentiero Muto",
        "flavor_it": "Le sue frecce furono le prime a non svegliare la bestia sotto i pini di Elfwood.",
        "tags": ["elfwood", "sentiero-muto"],
    },
    "sling-and-stones": {
        "it": "Fionda dei Sassi di Confine",
        "flavor_it": "I sassi vengono raccolti da entrambi i lati del confine, perché la fionda non riconosce stendardi.",
        "tags": ["confine", "viandanti"],
    },
    "torchbearer-cloak": {
        "it": "Mantello del Portatore di Brace",
        "flavor_it": "Odora di olio e pioggia; una brace resta accesa nell'orlo anche dopo il temporale.",
        "tags": ["fiaccole", "veglie"],
    },
    "torn-leather-vest": {
        "it": "Corpetto dello Strappo Ricucito",
        "flavor_it": "La cucitura segue il morso di qualcosa che i bestiari della Gilda non sanno nominare.",
        "tags": ["bestiari", "caccia"],
    },
    "training-buckler": {
        "it": "Brocchiere delle Cento Ammaccature",
        "flavor_it": "I maestri contano cento colpi sul legno; gli allievi ne trovano sempre uno in più.",
        "tags": ["cortile-darme", "addestramento"],
    },
    "training-shortsword": {
        "it": "Spada Corta del Cortile",
        "flavor_it": "Non ha mai versato sangue, ma conosce tutti gli errori commessi nel cortile d'arme.",
        "tags": ["cortile-darme", "addestramento"],
    },
    "travel_ration": {
        "it": "Razione della Lunga Veglia",
        "flavor_it": "Pane scuro, frutta secca e sale: la stessa porzione lasciata alle sentinelle della porta nord.",
        "tags": ["veglie", "porta-nord"],
    },
    "traveler-amulet": {
        "it": "Amuleto del Santo Sbiadito",
        "flavor_it": "Il volto è consumato, ma i viandanti continuano a riconoscere la strada indicata dal suo dito.",
        "tags": ["viandanti", "santi-dimenticati"],
    },
    "travelers-cloak": {
        "it": "Mantello delle Tasche Nascoste",
        "flavor_it": "Una tasca contiene sempre polvere di una città che il proprietario non ha ancora visitato.",
        "tags": ["viandanti", "città-lontane"],
    },
    "twine-bracelet": {
        "it": "Bracciale del Nodo di Via",
        "flavor_it": "Fu annodato a un santuario di strada; scioglierlo significa promettere di tornare.",
        "tags": ["santuari", "ritorni"],
    },
    "woolen-mantle": {
        "it": "Manto della Pecora di Brumacampo",
        "flavor_it": "Punge la pelle, ma trattiene il calore delle stalle di Brumacampo nelle notti senza luna.",
        "tags": ["brumacampo", "pastori"],
    },
}

# Lore-flavored display names for Epic+ (cherry-picked).
SLUG_DISPLAY_IT_EPIC_LEGENDARY: dict[str, dict] = {
    # We only hard-code a handful here; others get generic IT rarity-aware default.
    "voidpiercer-bow": {"it": "Arco Trafittore del Vuoto", "en": "Voidpiercer Bow",
                        "flavor_it": "Le frecce non sibilano. Vuotano.",
                        "tags": ["vuoto", "filo-spezzato"], "spoiler": "mystery"},
    "oracle-pendant": {"it": "Pendente dell'Oracolo Cieco", "en": "Blind Oracle's Pendant",
                       "flavor_it": "Vede ciò che non c'è ancora — e ciò che non c'è più.",
                       "tags": ["memoria", "oracolo"], "spoiler": "mystery"},
    "phoenix-relic": {"it": "Eco della Sinfonia dei Fili", "en": "Echo of the String Symphony",
                      "flavor_it": "Pulsa al ritmo di una nota silenziosa.",
                      "tags": ["sinfonia", "filo-spezzato"], "spoiler": "mystery"},
    "dragon-mask": {"it": "Maschera della Luna Morta", "en": "Mask of the Dead Moon",
                    "flavor_it": "Chi la indossa vede solo metà dei suoi nemici.",
                    "tags": ["luna-morta", "alevora"], "spoiler": "mystery"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_rarity(rarity: str | None) -> str:
    return _RARITY_CANONICAL.get(str(rarity or "Common").casefold(), "Common")


def _rarity_level(rarity: str | None) -> int:
    return _RARITY_LVL[_canonical_rarity(rarity)]


def _resolve_req_level(item: dict) -> int:
    base = _rarity_level(item.get("rarity") or "Common")
    if item.get("source") == "raid":
        base = max(base, 12)
    if (item.get("tags") or []) and "raid" in (item.get("tags") or []):
        base = max(base, 12)
    # Existing explicit value wins if higher.
    explicit = item.get("required_adventurer_level")
    if isinstance(explicit, int) and explicit > base:
        base = explicit
    return base


def _build_display_it(item: dict) -> tuple[str, str]:
    """Return (it, en) display names. Conservative auto-gen."""
    slug = item.get("slug") or ""
    if slug in COMMON_LORE_OVERRIDES:
        return (
            COMMON_LORE_OVERRIDES[slug]["it"],
            item.get("name") or slug.replace("-", " ").title(),
        )
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        d = SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug]
        return d["it"], d.get("en") or item.get("name") or slug
    # Auto: take english `name` and produce a plausible Italian-flavored variant.
    name = item.get("name") or slug.replace("-", " ").title()
    rarity = _canonical_rarity(item.get("rarity"))
    # Auto Italian common-translation: keep `name` as fallback,
    # but prefix lore-flavored adjective for Epic/Legendary.
    if rarity == "Legendary":
        it = f"{name} dell'Oblio"
    elif rarity == "Epic":
        it = f"{name} del Filo Spezzato"
    elif rarity == "Rare":
        it = f"{name} delle Veglie"
    elif rarity == "Uncommon":
        it = f"{name} del Confine"
    else:
        it = name  # Common: leave as-is
    return it, name


def _build_flavor(item: dict) -> tuple[str | None, str | None]:
    slug = item.get("slug") or ""
    if slug in COMMON_LORE_OVERRIDES:
        return COMMON_LORE_OVERRIDES[slug]["flavor_it"], None
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        d = SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug]
        return d.get("flavor_it"), d.get("flavor_en")
    rarity = _canonical_rarity(item.get("rarity"))
    if rarity == "Common":
        return None, None
    if rarity == "Uncommon":
        return ("Un oggetto di confine: parla solo a chi lo ascolta.", None)
    if rarity == "Rare":
        return ("Si sente una vibrazione antica, come una nota mai suonata.", None)
    if rarity == "Epic":
        return ("Porta in sé l'eco del Filo Spezzato. Vibra senza vento.", None)
    if rarity == "Legendary":
        return ("Ricorda un sigillo. Non quale.", None)
    return None, None


def _build_lore_tags(item: dict) -> list[str]:
    slug = item.get("slug") or ""
    if slug in COMMON_LORE_OVERRIDES:
        return list(COMMON_LORE_OVERRIDES[slug]["tags"])
    if slug in SLUG_DISPLAY_IT_EPIC_LEGENDARY:
        return SLUG_DISPLAY_IT_EPIC_LEGENDARY[slug].get("tags", [])
    rarity = _canonical_rarity(item.get("rarity"))
    if rarity == "Common":
        return ["mundane"]
    if rarity == "Uncommon":
        return ["frontiera"]
    if rarity == "Rare":
        return ["veglie", "memoria"]
    if rarity == "Epic":
        return ["filo-spezzato"]
    if rarity == "Legendary":
        return ["oblio", "vuoto"]
    return []


def _spoiler_level(item: dict) -> str:
    rarity = _canonical_rarity(item.get("rarity"))
    if rarity == "Legendary":
        return "mystery"
    return "public"


async def run() -> dict[str, Any]:
    flt = {
        "$and": [
            {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]},
            {"$or": [{"is_test": {"$ne": True}}, {"is_test": {"$exists": False}}]},
            {"$or": [{"slug": {"$not": {"$regex": "test|debug", "$options": "i"}}}]},
        ]
    }
    cursor = db.items.find(flt, {"_id": 0})
    updated = 0
    skipped = 0
    by_rarity: dict[str, int] = {}
    async for item in cursor:
        if item.get("lore_reviewed"):
            # Old Round-13a rows may have been enriched before rarity values
            # were normalised (for example ``epic`` instead of ``Epic``).
            # Reconcile only rows owned by this seed; canonical Hall lore has
            # its own names and intentional Lv1 override and must not change.
            if item.get("lore_source") == LORE_SOURCE:
                req_lvl = _resolve_req_level(item)
                disp_it, disp_en = _build_display_it(item)
                flavor_it, flavor_en = _build_flavor(item)
                desired: dict[str, Any] = {
                    "required_adventurer_level": req_lvl,
                    "display_name_it": disp_it,
                    "display_name_en": disp_en,
                    "lore_tags": _build_lore_tags(item),
                    "spoiler_level": _spoiler_level(item),
                }
                if flavor_it is not None:
                    desired["flavor_text_it"] = flavor_it
                if flavor_en is not None:
                    desired["flavor_text_en"] = flavor_en
                corrections = {
                    key: value
                    for key, value in desired.items()
                    if item.get(key) != value
                }
                if corrections:
                    corrections["lore_reviewed_at"] = _now()
                    await db.items.update_one(
                        {"slug": item["slug"]},
                        {"$set": corrections},
                    )
                    updated += 1
                    rar = _canonical_rarity(item.get("rarity"))
                    by_rarity[rar] = by_rarity.get(rar, 0) + 1
                    continue
            skipped += 1
            continue
        req_lvl = _resolve_req_level(item)
        disp_it, disp_en = _build_display_it(item)
        flavor_it, flavor_en = _build_flavor(item)
        set_fields: dict[str, Any] = {
            "required_adventurer_level": req_lvl,
            "display_name_it": disp_it,
            "display_name_en": disp_en,
            "lore_tags": _build_lore_tags(item),
            "lore_source": LORE_SOURCE,
            "lore_reviewed": True,
            "lore_reviewed_at": _now(),
            "spoiler_level": _spoiler_level(item),
        }
        if flavor_it is not None:
            set_fields["flavor_text_it"] = flavor_it
        if flavor_en is not None:
            set_fields["flavor_text_en"] = flavor_en
        await db.items.update_one({"slug": item["slug"]}, {"$set": set_fields})
        updated += 1
        rar = _canonical_rarity(item.get("rarity"))
        by_rarity[rar] = by_rarity.get(rar, 0) + 1

    out = {
        "status": "done",
        "items_updated": updated,
        "items_skipped_already_reviewed": skipped,
        "by_rarity": by_rarity,
    }
    logger.info("ROUND 13a items lore+level: %s", out)
    return out


if __name__ == "__main__":
    print(asyncio.run(run()))
