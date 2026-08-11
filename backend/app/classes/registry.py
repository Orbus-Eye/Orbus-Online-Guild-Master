"""FASE 9B — Registry canonico delle 27 classi (Source of Truth).

Nuovo modello:

    AVVENTURIERO → CLASSE → RUOLO FISSO → EQUIP DI CLASSE → SET RAID

Il ruolo (`class_role`) deriva SEMPRE dalla classe: niente
specializzazioni selezionabili, niente build. La vecchia tassonomia
(Tank/DPS/Support/Hybrid/Utility del catalogo Hall e dei doc
`adventurer_classes`) è sostituita a runtime da questo registry.

Distribuzione canonica (mandato FASE 9): 13 DPS · 6 TANK · 8 HEALER.

PUNTO DI ESTENSIONE FUTURO (non implementato in questa tranche):
`hybrid_slot` — lo "SLOT DI CLASSE" che permetterà una piccola
componente ibrida per classe. Oggi è SEMPRE None; l'architettura è
pronta perché l'aggiunta futura non richieda refactor (basterà popolare
il campo e agganciare il validatore equip).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType

CLASS_ROLE_DPS = "DPS"
CLASS_ROLE_TANK = "TANK"
CLASS_ROLE_HEALER = "HEALER"

CANONICAL_ROLES = (CLASS_ROLE_DPS, CLASS_ROLE_TANK, CLASS_ROLE_HEALER)

# Etichette player-facing IT (il codice usa i valori canonici EN-caps).
ROLE_LABEL_IT = {
    CLASS_ROLE_DPS: "Danno",
    CLASS_ROLE_TANK: "Difensore",
    CLASS_ROLE_HEALER: "Guaritore",
}


@dataclass(frozen=True, slots=True)
class ClassDefinition:
    class_id: str                 # slug canonico (== canonical_class_slug Hall)
    class_name: str               # nome italiano player-facing
    class_role: str               # DPS | TANK | HEALER — FISSO
    class_identity: str           # identità narrativa breve (IT)
    class_mechanics: str          # descrizione gameplay coerente col ruolo (IT)
    primary_stat: str             # stat primaria storica della classe
    armor_tags: tuple[str, ...]   # regole equip (dal catalogo Hall)
    weapon_tags: tuple[str, ...]
    emblem: str                   # slug asset emblema (assets/classes/{emblem}.svg)
    emblem_symbol: str            # identity map: simbolo distintivo (IT)
    palette: tuple[str, str]      # (colore base, accento) per card/banner
    strengths: tuple[str, ...] = ()   # punti di forza player-facing (IT)
    hybrid_slot: None = field(default=None)  # FUTURO: slot di classe (mai usato oggi)


def _c(**kw) -> ClassDefinition:
    kw.setdefault("emblem", kw["class_id"])
    return ClassDefinition(**kw)


_DEFINITIONS: tuple[ClassDefinition, ...] = (
    # ── DPS (13) ────────────────────────────────────────────────────────
    _c(class_id="guerriero", class_name="Guerriero", class_role=CLASS_ROLE_DPS,
       class_identity="L'acciaio non si spezza. Si tempra.",
       class_mechanics="Maestro d'armi in prima linea: pressione costante, "
                       "colpi pesanti e fendenti che spezzano il fronte nemico.",
       primary_stat="strength",
       armor_tags=("mail", "plate"),
       weapon_tags=("sword", "axe", "hammer", "spear", "polearm"),
       emblem_symbol="due spade incrociate su campo d'acciaio",
       palette=("#7f1d1d", "#f59e0b"),
       strengths=("Danno costante in mischia", "Tenuta in prima linea",
                  "Nessuna risorsa da gestire")),
    _c(class_id="ladro", class_name="Ladro", class_role=CLASS_ROLE_DPS,
       class_identity="Un passo taciuto vale più di cento minacce.",
       class_mechanics="Assalti dall'ombra: aperture rapide, colpi critici "
                       "ed elusione. Punisce chi abbassa la guardia.",
       primary_stat="agility",
       armor_tags=("leather",),
       weapon_tags=("dagger", "sword", "crossbow"),
       emblem_symbol="pugnale nell'ombra di una maschera",
       palette=("#1e293b", "#94a3b8"),
       strengths=("Colpi critici", "Elusione", "Disinnesco di trappole")),
    _c(class_id="mago", class_name="Mago", class_role=CLASS_ROLE_DPS,
       class_identity="Ogni sigillo custodisce una domanda più pericolosa della risposta.",
       class_mechanics="Incantatore puro: esplosioni arcane, controllo del "
                       "campo e dissoluzione delle barriere magiche.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("staff", "tome", "focus", "dagger"),
       emblem_symbol="sigillo arcano a nove punte",
       palette=("#312e81", "#818cf8"),
       strengths=("Danno ad area", "Contrasto alle barriere magiche",
                  "Potenza pura")),
    _c(class_id="monaco", class_name="Monaco", class_role=CLASS_ROLE_DPS,
       class_identity="Il corpo è la prima disciplina.",
       class_mechanics="Combo senz'armi, mobilità estrema e recupero tramite "
                       "disciplina interiore.",
       primary_stat="agility",
       armor_tags=("cloth", "leather"),
       weapon_tags=("fist", "staff"),
       emblem_symbol="pugno cinto da una corda annodata",
       palette=("#9a3412", "#fdba74"),
       strengths=("Raffiche di colpi", "Mobilità", "Autosufficienza")),
    _c(class_id="negromante", class_name="Negromante", class_role=CLASS_ROLE_DPS,
       class_identity="Ciò che è finito continua se sa il proprio nome.",
       class_mechanics="Necroenergia e logoramento: servitori non morti che "
                       "consumano il nemico un istante alla volta.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("staff", "tome", "dagger"),
       emblem_symbol="teschio dentro un cerchio chiuso",
       palette=("#14532d", "#86efac"),
       strengths=("Danno nel tempo", "Servitori", "Contrasto ai non morti")),
    _c(class_id="cacciatore_del_vuoto", class_name="Cacciatore del Vuoto",
       class_role=CLASS_ROLE_DPS,
       class_identity="Si caccia ciò che non ha peso.",
       class_mechanics="Tiro a lunga distanza e dissoluzione: l'unica lama "
                       "che morde gli incorporei.",
       primary_stat="intellect",
       armor_tags=("cloth", "leather"),
       weapon_tags=("bow", "crossbow", "focus"),
       emblem_symbol="occhio-lanterna nel vuoto stellato",
       palette=("#2e1065", "#c4b5fd"),
       strengths=("Danno a distanza", "Contrasto agli incorporei",
                  "Visione nel buio")),
    _c(class_id="artificiere", class_name="Artificiere", class_role=CLASS_ROLE_DPS,
       class_identity="Ciò che si rompe si rifà; ciò che si rifà migliora.",
       class_mechanics="Torrette, ordigni e dispositivi: danno meccanico "
                       "programmato che non conosce stanchezza.",
       primary_stat="agility",
       armor_tags=("leather", "mail"),
       weapon_tags=("hammer", "crossbow", "focus"),
       emblem_symbol="ingranaggio attraversato da una chiave inglese",
       palette=("#78350f", "#fbbf24"),
       strengths=("Danno costante da torrette", "Ordigni ad area",
                  "Precisione meccanica")),
    _c(class_id="cartografo", class_name="Cartografo", class_role=CLASS_ROLE_DPS,
       class_identity="La mappa non descrive, la mappa ricorda.",
       class_mechanics="Conosce il terreno prima del nemico: colpi di "
                       "precisione dove la mappa dice che il nemico sarà.",
       primary_stat="agility",
       armor_tags=("cloth", "leather"),
       weapon_tags=("dagger", "crossbow", "focus"),
       emblem_symbol="rosa dei venti incisa su pergamena",
       palette=("#374151", "#fde68a"),
       strengths=("Colpi di precisione", "Vantaggio di posizione",
                  "Esplorazione")),
    _c(class_id="runista", class_name="Runista", class_role=CLASS_ROLE_DPS,
       class_identity="La runa non descrive, la runa impone.",
       class_mechanics="Rune incise che detonano ad area: il danno è già "
                       "scritto, il nemico deve solo passarci sopra.",
       primary_stat="intellect",
       armor_tags=("cloth", "mail"),
       weapon_tags=("staff", "hammer", "focus"),
       emblem_symbol="runa spezzata che sprigiona luce",
       palette=("#0c4a6e", "#7dd3fc"),
       strengths=("Detonazioni ad area", "Trappole runiche",
                  "Dissoluzione")),
    _c(class_id="burattinaio", class_name="Burattinaio", class_role=CLASS_ROLE_DPS,
       class_identity="Il filo che tiene è il filo che libera.",
       class_mechanics="Marionette da guerra manovrate a distanza: il danno "
                       "arriva da fili che nessuno vede.",
       primary_stat="agility",
       armor_tags=("cloth", "leather"),
       weapon_tags=("dagger", "crossbow", "focus"),
       emblem_symbol="maschera teatrale sospesa a fili incrociati",
       palette=("#4c0519", "#fda4af"),
       strengths=("Danno a distanza tramite marionette", "Controllo",
                  "Imprevedibilità")),
    _c(class_id="giocatore_d_azzardo", class_name="Giocatore d'Azzardo",
       class_role=CLASS_ROLE_DPS,
       class_identity="La sorte è un patto scritto in nero.",
       class_mechanics="Rischio calcolato: colpi che possono raddoppiare, "
                       "dadi che decidono chi sanguina.",
       primary_stat="agility",
       armor_tags=("cloth", "leather"),
       weapon_tags=("dagger", "crossbow", "focus"),
       emblem_symbol="due dadi d'ossidiana sul tredici impossibile",
       palette=("#171717", "#facc15"),
       strengths=("Picchi di danno", "Rischio/ricompensa",
                  "Fortuna sfacciata")),
    _c(class_id="pittore", class_name="Pittore", class_role=CLASS_ROLE_DPS,
       class_identity="Il colore giusto costa.",
       class_mechanics="Immagini viventi che azzannano la tela del mondo: "
                       "ritratti debilitanti e pennellate che feriscono.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("focus", "staff", "dagger"),
       emblem_symbol="pennello che gocciola un colore vivo",
       palette=("#701a75", "#f0abfc"),
       strengths=("Danno psichico", "Illusioni", "Debuff dipinti")),
    _c(class_id="cacciatore_del_sangue", class_name="Cacciatore del Sangue",
       class_role=CLASS_ROLE_DPS,
       class_identity="Il sangue sa dove torna.",
       class_mechanics="Emorragia e inseguimento: più la preda è ferita, più "
                       "i suoi colpi affondano.",
       primary_stat="strength",
       armor_tags=("leather", "mail"),
       weapon_tags=("axe", "sword", "spear"),
       emblem_symbol="zanna bianca su goccia di sangue",
       palette=("#450a0a", "#fca5a5"),
       strengths=("Sanguinamento", "Esecuzione delle prede ferite",
                  "Sostentamento")),
    # ── TANK (6) ────────────────────────────────────────────────────────
    _c(class_id="paladino", class_name="Paladino", class_role=CLASS_ROLE_TANK,
       class_identity="La luce resta quando il voto costa più della vittoria.",
       class_mechanics="Baluardo consacrato: scudo, voto e luce fissa. "
                       "Attira i colpi e li restituisce come giudizio.",
       primary_stat="faith",
       armor_tags=("mail", "plate"),
       weapon_tags=("hammer", "shield", "relic", "focus"),
       emblem_symbol="scudo con fiamma sacra al centro",
       palette=("#713f12", "#fde047"),
       strengths=("Protezione sacra", "Presa degli attacchi nemici",
                  "Contrasto a non morti e maledizioni")),
    _c(class_id="cacciatore_di_mostri", class_name="Cacciatore di Mostri",
       class_role=CLASS_ROLE_TANK,
       class_identity="La pista parla soltanto a chi smette di inseguire il rumore.",
       class_mechanics="Conosce la preda meglio di sé: la aggancia, la "
                       "trattiene e ne assorbe la furia mentre il branco colpisce.",
       primary_stat="endurance",
       armor_tags=("leather", "mail"),
       weapon_tags=("spear", "sword", "crossbow", "shield"),
       emblem_symbol="testa di bestia trafitta da una lancia",
       palette=("#3f2d20", "#d6a463"),
       strengths=("Aggancio delle bestie", "Trappole difensive",
                  "Conoscenza dei mostri")),
    _c(class_id="fabbro_arcano", class_name="Fabbro Arcano", class_role=CLASS_ROLE_TANK,
       class_identity="Il metallo tace ma ricorda.",
       class_mechanics="Corazza runica autoriparante: ogni colpo subito "
                       "incide una runa che restituisce protezione.",
       primary_stat="strength",
       armor_tags=("mail", "plate"),
       weapon_tags=("hammer", "axe", "shield", "focus"),
       emblem_symbol="incudine con runa incandescente",
       palette=("#334155", "#fb923c"),
       strengths=("Mitigazione runica", "Armatura pesante",
                  "Riparazione in battaglia")),
    _c(class_id="parassita", class_name="Parassita", class_role=CLASS_ROLE_TANK,
       class_identity="Si vive di ciò che si trova.",
       class_mechanics="Drena vigore dai nemici per rigenerare il proprio: "
                       "più viene colpito, più radica e resiste.",
       primary_stat="endurance",
       armor_tags=("cloth", "leather"),
       weapon_tags=("dagger", "fist", "sickle"),
       emblem_symbol="radice cava avvolta a spirale",
       palette=("#1a2e05", "#a3e635"),
       strengths=("Drenaggio e autorigenerazione", "Tenuta prolungata",
                  "Logoramento")),
    _c(class_id="cavaliere_della_morte", class_name="Cavaliere della Morte",
       class_role=CLASS_ROLE_TANK,
       class_identity="La morte è già passata, io la seguo.",
       class_mechanics="Tenuta oltre la vita: vessillo nero, aura di paura e "
                       "necroenergia che rifiuta di cadere.",
       primary_stat="endurance",
       armor_tags=("mail", "plate"),
       weapon_tags=("sword", "axe", "shield"),
       emblem_symbol="elmo nero sotto un vessillo strappato",
       palette=("#18181b", "#a1a1aa"),
       strengths=("Aura di paura", "Tenuta oltre la morte",
                  "Necroenergia difensiva")),
    _c(class_id="cavaliere_di_draghi", class_name="Cavaliere di Draghi",
       class_role=CLASS_ROLE_TANK,
       class_identity="Il drago non si comanda, si accompagna.",
       class_mechanics="Avanguardia in scaglie di drago: carica, presenza "
                       "draconica e fiamma che tiene il fronte.",
       primary_stat="strength",
       armor_tags=("mail", "plate"),
       weapon_tags=("spear", "sword", "shield"),
       emblem_symbol="drago avvolto attorno a una lancia",
       palette=("#7c2d12", "#f97316"),
       strengths=("Carica di sfondamento", "Scaglie draconiche",
                  "Presenza che intimidisce")),
    # ── HEALER (8) ──────────────────────────────────────────────────────
    _c(class_id="alchimista", class_name="Alchimista", class_role=CLASS_ROLE_HEALER,
       class_identity="Un grammo separa cura e veleno.",
       class_mechanics="Pozioni, distillati e rimedi: cura misurata al "
                       "grammo e antidoti per ogni ferita.",
       primary_stat="intellect",
       armor_tags=("cloth", "leather"),
       weapon_tags=("dagger", "focus", "vial"),
       emblem_symbol="alambicco dal vapore verde",
       palette=("#064e3b", "#6ee7b7"),
       strengths=("Cure con pozioni", "Antidoti", "Buff di preparazione")),
    _c(class_id="bardo", class_name="Bardo", class_role=CLASS_ROLE_HEALER,
       class_identity="Una canzone rimasta a metà è un patto.",
       class_mechanics="Armonie che ricuciono: il morale del gruppo è la "
                       "prima medicina, la canzone la seconda.",
       primary_stat="faith",
       armor_tags=("cloth", "leather"),
       weapon_tags=("instrument", "rapier", "dagger"),
       emblem_symbol="lira con una corda spezzata",
       palette=("#581c87", "#d8b4fe"),
       strengths=("Cure corali", "Morale di gruppo", "Debuff sonori")),
    _c(class_id="druido", class_name="Druido", class_role=CLASS_ROLE_HEALER,
       class_identity="La foresta chiede prima di dare.",
       class_mechanics="Guarigione naturale: linfa, rigenerazione e la "
                       "pazienza millenaria del salice.",
       primary_stat="faith",
       armor_tags=("cloth", "leather"),
       weapon_tags=("staff", "sickle", "totem"),
       emblem_symbol="salice con radici a cerchio",
       palette=("#14532d", "#4ade80"),
       strengths=("Rigenerazione", "Cure nel tempo", "Armonia naturale")),
    _c(class_id="sciamano", class_name="Sciamano", class_role=CLASS_ROLE_HEALER,
       class_identity="Lo spirito non parla, lo spirito ricorda.",
       class_mechanics="Cura elementale e totem: gli spiriti sostengono chi "
                       "il tamburo chiama per nome.",
       primary_stat="faith",
       armor_tags=("cloth", "leather"),
       weapon_tags=("staff", "totem", "mace"),
       emblem_symbol="tamburo rituale con piuma",
       palette=("#7c2d12", "#5eead4"),
       strengths=("Cure totemiche", "Sostegno elementale",
                  "Memoria degli spiriti")),
    _c(class_id="cronista", class_name="Cronista", class_role=CLASS_ROLE_HEALER,
       class_identity="Ciò che viene scritto oggi accade oggi per sempre.",
       class_mechanics="Riscrive le ferite come refusi: ciò che la penna "
                       "corregge, il corpo dimentica.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("tome", "focus", "dagger"),
       emblem_symbol="penna d'oca su pergamena sigillata",
       palette=("#44403c", "#e7e5e4"),
       strengths=("Correzione delle ferite", "Informazione",
                  "Sostegno investigativo")),
    _c(class_id="mercante", class_name="Mercante", class_role=CLASS_ROLE_HEALER,
       class_identity="Il prezzo giusto è quello che entrambi accettano.",
       class_mechanics="Rifornimenti, scorte e contratti di soccorso: nessuna "
                       "ferita resta aperta se il prezzo è onesto.",
       primary_stat="agility",
       armor_tags=("cloth", "leather"),
       weapon_tags=("rapier", "crossbow", "dagger"),
       emblem_symbol="bilancia in equilibrio perfetto",
       palette=("#713f12", "#fcd34d"),
       strengths=("Rifornimenti sul campo", "Scorte di emergenza",
                  "Sostegno economico")),
    _c(class_id="astrologo", class_name="Astrologo", class_role=CLASS_ROLE_HEALER,
       class_identity="Ciò che è scritto in alto è già accaduto in basso.",
       class_mechanics="Legge le ferite prima che accadano: previsione, fasi "
                       "astrali e destini raddrizzati.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("staff", "focus", "tome"),
       emblem_symbol="costellazione a tredici tacche",
       palette=("#1e1b4b", "#a5b4fc"),
       strengths=("Prevenzione dei colpi", "Cure predette",
                  "Debuff cosmici")),
    _c(class_id="sognatore", class_name="Sognatore", class_role=CLASS_ROLE_HEALER,
       class_identity="Il sogno è già accaduto, solo non lo sappiamo.",
       class_mechanics="Ripara nel sogno ciò che il giorno ha rotto: presenze "
                       "oniriche che vegliano sul gruppo.",
       primary_stat="intellect",
       armor_tags=("cloth",),
       weapon_tags=("focus", "tome", "staff"),
       emblem_symbol="mezzaluna su occhio chiuso",
       palette=("#0f172a", "#93c5fd"),
       strengths=("Cure oniriche", "Veglia psichica", "Sollievo mentale")),
)

CLASS_REGISTRY: MappingProxyType[str, ClassDefinition] = MappingProxyType(
    {definition.class_id: definition for definition in _DEFINITIONS}
)

# Slug legacy (pre-Round 16.0, inglesi) → slug canonico. Allineato a
# `legacy_class_slugs` del catalogo Class Hall + classi ritirate
# (berserker/assassin) mappate sulla parente più vicina.
LEGACY_CLASS_SLUG_ALIASES: MappingProxyType[str, str] = MappingProxyType({
    "warrior": "guerriero",
    "berserker": "guerriero",
    "rogue": "ladro",
    "assassin": "ladro",
    "mage": "mago",
    "paladin": "paladino",
    "priest": "paladino",
    "ranger": "cacciatore_di_mostri",
    "alchemist": "alchimista",
    "bard": "bardo",
    "druid": "druido",
    "monk": "monaco",
    "necromancer": "negromante",
    "shaman": "sciamano",
    "void_hunter": "cacciatore_del_vuoto",
    "warlock": "cacciatore_del_vuoto",
    "artificer": "artificiere",
    "cartographer": "cartografo",
    "chronicler": "cronista",
    "arcane_smith": "fabbro_arcano",
    "merchant": "mercante",
    "runist": "runista",
    "astrologer": "astrologo",
    "puppeteer": "burattinaio",
    "gambler": "giocatore_d_azzardo",
    "parasite": "parassita",
    "painter": "pittore",
    "dreamer": "sognatore",
    "blood_hunter": "cacciatore_del_sangue",
    "death_knight": "cavaliere_della_morte",
    "dragon_knight": "cavaliere_di_draghi",
})

# Vecchi valori di ruolo (doc `adventurer_classes` / snapshot storici) →
# ruolo canonico. Support/Hybrid/Utility NON sono mappabili senza slug
# (ambigui per design): in quei casi fa fede la classe.
_LEGACY_ROLE_VALUES = {
    "dps": CLASS_ROLE_DPS,
    "tank": CLASS_ROLE_TANK,
    "healer": CLASS_ROLE_HEALER,
}

# Mapping ruolo → stat di focalizzazione per equipment/set (stat REALI
# del runtime: strength/agility/intellect/endurance/faith).
_ROLE_FOCUS = {
    CLASS_ROLE_DPS: ("primary", "agility"),      # danno: stat primaria + agilità
    CLASS_ROLE_TANK: ("endurance", "primary"),   # mitigazione: END prima di tutto
    CLASS_ROLE_HEALER: ("faith", "primary"),     # cura/supporto: FAI + primaria
}


def canonical_class_slug(class_slug: str) -> str | None:
    slug = (class_slug or "").strip().lower()
    if slug in CLASS_REGISTRY:
        return slug
    return LEGACY_CLASS_SLUG_ALIASES.get(slug)


def registry_entry(class_slug: str) -> ClassDefinition | None:
    resolved = canonical_class_slug(class_slug)
    return CLASS_REGISTRY.get(resolved) if resolved else None


def class_role_for(class_slug: str) -> str | None:
    """Ruolo canonico e FISSO della classe (None se slug sconosciuto).
    Risolve anche gli slug legacy inglesi."""
    entry = registry_entry(class_slug)
    return entry.class_role if entry else None


def normalize_role_value(value: str | None) -> str | None:
    """Normalizza un valore di ruolo storico ("Tank", "dps", …) al
    canone DPS/TANK/HEALER. Support/Hybrid/Utility → None (serve lo slug)."""
    return _LEGACY_ROLE_VALUES.get((value or "").strip().lower())


def member_role(member: dict) -> str | None:
    """Ruolo canonico di un membro squadra/snapshot: prima la CLASSE
    (source of truth), poi i campi ruolo storici come fallback."""
    for key in ("class_slug", "canonical_class_slug", "class_name"):
        role = class_role_for(str(member.get(key) or ""))
        if role:
            return role
    for key in ("class_role", "role_snapshot"):
        role = normalize_role_value(member.get(key))
        if role:
            return role
    return None


def role_focus_stats(class_slug: str) -> tuple[str, str]:
    """Coppia (stat principale, stat secondaria) per item/set della classe.

    Usa SOLO statistiche reali del runtime. "primary" viene risolto nella
    primary_stat storica della classe; mai due volte la stessa stat.
    """
    entry = registry_entry(class_slug)
    if entry is None:
        return ("endurance", "strength")
    first, second = _ROLE_FOCUS[entry.class_role]
    resolved_first = entry.primary_stat if first == "primary" else first
    resolved_second = entry.primary_stat if second == "primary" else second
    if resolved_second == resolved_first:
        resolved_second = "endurance" if resolved_first != "endurance" else "strength"
    return (resolved_first, resolved_second)


def role_counts() -> dict[str, int]:
    counts = {role: 0 for role in CANONICAL_ROLES}
    for definition in CLASS_REGISTRY.values():
        counts[definition.class_role] += 1
    return counts


__all__ = [
    "CANONICAL_ROLES",
    "CLASS_REGISTRY",
    "CLASS_ROLE_DPS",
    "CLASS_ROLE_HEALER",
    "CLASS_ROLE_TANK",
    "ClassDefinition",
    "LEGACY_CLASS_SLUG_ALIASES",
    "ROLE_LABEL_IT",
    "canonical_class_slug",
    "class_role_for",
    "member_role",
    "normalize_role_value",
    "registry_entry",
    "role_counts",
    "role_focus_stats",
]
