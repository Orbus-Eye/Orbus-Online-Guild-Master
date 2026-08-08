"""Wave-A-E class mechanics and item-driven build identities.

This is a pure, deterministic class contract.  Class identity supplies a
small baseline bonus; equipped item tags select one of three builds and
activate the larger resonance bonus.  Database rows cannot define executable
mechanics: they only expose already-validated equipment tags.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class BuildIdentity:
    build_id: str
    name_it: str
    description_it: str
    item_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClassMechanic:
    mechanic_id: str
    class_slug: str
    name_it: str
    summary_it: str
    primary_stat: str
    counter_tags: tuple[str, ...]
    builds: tuple[BuildIdentity, ...]
    wave: str = "A"


WAVE_A_CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "guerriero": ClassMechanic(
        "class.guerriero.tempra",
        "guerriero",
        "Tempra della Linea",
        "Il Guerriero trasforma l'equipaggiamento marziale in tenuta frontale.",
        "endurance",
        ("counter_boss", "counter_siege"),
        (
            BuildIdentity(
                "bastione", "Bastione",
                "Scudo e armatura per reggere la linea.",
                ("shield", "plate"),
            ),
            BuildIdentity(
                "assaltatore", "Assaltatore",
                "Armi pesanti per spezzare il fronte.",
                ("axe", "hammer", "polearm"),
            ),
            BuildIdentity(
                "condottiero", "Condottiero",
                "Spada o lancia per guidare l'avanzata.",
                ("sword", "spear"),
            ),
        ),
    ),
    "ladro": ClassMechanic(
        "class.ladro.slancio",
        "ladro",
        "Slancio nell'Ombra",
        "Il Ladro converte la scelta dell'arma in apertura, elusione e sabotaggio.",
        "agility",
        ("counter_trap", "counter_stealth"),
        (
            BuildIdentity(
                "ombra", "Ombra",
                "Pugnali e colpi che non lasciano traccia.", ("dagger",),
            ),
            BuildIdentity(
                "duellante", "Duellante",
                "Lama singola, ritmo e contrattacco.", ("sword", "rapier"),
            ),
            BuildIdentity(
                "sabotatore", "Sabotatore",
                "Balestra e strumenti contro trappole.", ("crossbow",),
            ),
        ),
    ),
    "mago": ClassMechanic(
        "class.mago.risonanza",
        "mago",
        "Risonanza dei Sigilli",
        "Il Mago accorda il proprio sapere al tramite arcano equipaggiato.",
        "intellect",
        ("counter_spell", "counter_magic_barrier"),
        (
            BuildIdentity(
                "arcanista", "Arcanista",
                "Bastone e potenza arcana diretta.", ("staff",),
            ),
            BuildIdentity(
                "sigillatore", "Sigillatore",
                "Focus e controllo delle barriere.", ("focus",),
            ),
            BuildIdentity(
                "sapiente", "Sapiente",
                "Tomi, memoria e preparazione.", ("tome",),
            ),
        ),
    ),
    "paladino": ClassMechanic(
        "class.paladino.voto",
        "paladino",
        "Voto della Luce Fissa",
        "Il Paladino converte il proprio equipaggiamento in protezione consacrata.",
        "faith",
        ("counter_undead", "counter_curse"),
        (
            BuildIdentity(
                "custode", "Custode",
                "Martello e presenza protettiva.", ("hammer",),
            ),
            BuildIdentity(
                "ierofante", "Ierofante",
                "Vesti e bastone per sostenere il gruppo.",
                ("cloth", "staff"),
            ),
            BuildIdentity(
                "reliquiario", "Reliquiario",
                "Reliquie e focus contro empietà e maledizioni.",
                ("relic", "focus"),
            ),
        ),
    ),
    "cacciatore_di_mostri": ClassMechanic(
        "class.cacciatore_di_mostri.predazione",
        "cacciatore_di_mostri",
        "Studio della Preda",
        "Il Cacciatore legge la minaccia attraverso l'arma scelta.",
        "agility",
        ("counter_beast", "counter_ambush"),
        (
            BuildIdentity(
                "tiratore", "Tiratore",
                "Arco, distanza e punto debole.", ("bow",),
            ),
            BuildIdentity(
                "trappolatore", "Trappolatore",
                "Balestra e controllo del terreno.", ("crossbow",),
            ),
            BuildIdentity(
                "inseguitore", "Inseguitore",
                "Lama o lancia per non perdere la pista.",
                ("sword", "dagger", "spear"),
            ),
        ),
    ),
}

WAVE_B_CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "alchimista": ClassMechanic(
        "class.alchimista.dosaggio",
        "alchimista",
        "Dosaggio Esatto",
        "L'Alchimista decide se ogni preparato debba curare, corrodere o mutare.",
        "intellect",
        ("counter_poison", "counter_disease"),
        (
            BuildIdentity(
                "cerusico", "Cerusico",
                "Fiale e preparati per stabilizzare la squadra.", ("vial",),
            ),
            BuildIdentity(
                "tossicologo", "Tossicologo",
                "Pugnale e composti per indebolire il nemico.", ("dagger",),
            ),
            BuildIdentity(
                "trasmutatore", "Trasmutatore",
                "Focus e reagenti per alterare il campo.", ("focus",),
            ),
        ),
        wave="B",
    ),
    "bardo": ClassMechanic(
        "class.bardo.armonia",
        "bardo",
        "Armonia Incompiuta",
        "Il Bardo trasforma ritmo, presenza e lama in vantaggio condiviso.",
        "faith",
        ("counter_spell", "counter_curse"),
        (
            BuildIdentity(
                "cantore", "Cantore",
                "Strumenti e armonie per sostenere il gruppo.",
                ("instrument",),
            ),
            BuildIdentity(
                "duellista", "Duellista",
                "Stocco, tempo e provocazione.", ("rapier",),
            ),
            BuildIdentity(
                "sussurratore", "Sussurratore",
                "Pugnale e note spezzate contro rituali ostili.", ("dagger",),
            ),
        ),
        wave="B",
    ),
    "druido": ClassMechanic(
        "class.druido.ciclo",
        "druido",
        "Ciclo del Salice",
        "Il Druido adatta il proprio ciclo a crescita, predazione o custodia.",
        "faith",
        ("counter_beast", "counter_elemental"),
        (
            BuildIdentity(
                "custode", "Custode del Bosco",
                "Bastone e crescita per proteggere la squadra.", ("staff",),
            ),
            BuildIdentity(
                "predatore", "Predatore Verde",
                "Falce e istinto per inseguire la preda.", ("sickle",),
            ),
            BuildIdentity(
                "totemista", "Totemista",
                "Totem e ascolto degli elementi.", ("totem",),
            ),
        ),
        wave="B",
    ),
    "monaco": ClassMechanic(
        "class.monaco.disciplina",
        "monaco",
        "Disciplina di Cinabro",
        "Il Monaco converte continuità e postura in pressione controllata.",
        "agility",
        ("counter_boss", "counter_trap"),
        (
            BuildIdentity(
                "pugno_vuoto", "Pugno Vuoto",
                "Armi da pugno e sequenze ravvicinate.", ("fist",),
            ),
            BuildIdentity(
                "bastone_circolare", "Bastone Circolare",
                "Bastone, portata e controllo del ritmo.", ("staff",),
            ),
            BuildIdentity(
                "asceta", "Asceta",
                "Vesti leggere e disciplina difensiva.", ("cloth",),
            ),
        ),
        wave="B",
    ),
    "negromante": ClassMechanic(
        "class.negromante.memoria",
        "negromante",
        "Memoria del Cerchio",
        "Il Negromante sceglie se comandare, ricordare o recidere i morti.",
        "intellect",
        ("counter_undead", "counter_void"),
        (
            BuildIdentity(
                "evocatore", "Evocatore",
                "Bastone e autorità sui servitori.", ("staff",),
            ),
            BuildIdentity(
                "onomante", "Onomante",
                "Tomo e nomi veri per vincolare i morti.", ("tome",),
            ),
            BuildIdentity(
                "mietitore", "Mietitore",
                "Pugnale e recisione dei legami necrotici.", ("dagger",),
            ),
        ),
        wave="B",
    ),
    "sciamano": ClassMechanic(
        "class.sciamano.risonanza_spiriti",
        "sciamano",
        "Risonanza degli Spiriti",
        "Lo Sciamano accorda il gruppo a spirito, elemento o memoria.",
        "faith",
        ("counter_elemental", "counter_disease"),
        (
            BuildIdentity(
                "veggente", "Veggente",
                "Bastone e ascolto degli spiriti lontani.", ("staff",),
            ),
            BuildIdentity(
                "totemista", "Totemista",
                "Totem e protezione persistente.", ("totem",),
            ),
            BuildIdentity(
                "tempestario", "Tempestario",
                "Mazza e richiamo violento degli elementi.", ("mace",),
            ),
        ),
        wave="B",
    ),
    "cacciatore_del_vuoto": ClassMechanic(
        "class.cacciatore_del_vuoto.ancoraggio",
        "cacciatore_del_vuoto",
        "Ancoraggio del Riflesso",
        "Il Cacciatore del Vuoto fissa ciò che non possiede peso né ombra.",
        "intellect",
        ("counter_void", "counter_magic_barrier"),
        (
            BuildIdentity(
                "arciere_del_faro", "Arciere del Faro",
                "Arco e traiettorie contro bersagli incorporei.", ("bow",),
            ),
            BuildIdentity(
                "dissolutore", "Dissolutore",
                "Balestra e munizioni che rompono il riflesso.", ("crossbow",),
            ),
            BuildIdentity(
                "ancoratore", "Ancoratore",
                "Focus e sigilli che danno peso al Vuoto.", ("focus",),
            ),
        ),
        wave="B",
    ),
}

WAVE_C_CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "artificiere": ClassMechanic(
        "class.artificiere.protocollo",
        "artificiere",
        "Protocollo Modulare",
        "L'Artificiere riconfigura il proprio dispositivo prima di ogni impresa.",
        "agility",
        ("counter_siege", "counter_trap"),
        (
            BuildIdentity(
                "ingegnere", "Ingegnere da Campo",
                "Martello e riparazioni per mantenere la linea.",
                ("hammer",),
            ),
            BuildIdentity(
                "bombardiere", "Bombardiere",
                "Balestra e cariche per smontare difese e congegni.",
                ("crossbow",),
            ),
            BuildIdentity(
                "sintonizzatore", "Sintonizzatore",
                "Focus e calibrazione per governare dispositivi arcani.",
                ("focus",),
            ),
        ),
        wave="C",
    ),
    "cartografo": ClassMechanic(
        "class.cartografo.rotta",
        "cartografo",
        "Rotta Memorizzata",
        "Il Cartografo converte ogni strumento in una via sicura nell'ignoto.",
        "agility",
        ("counter_ambush", "counter_trap"),
        (
            BuildIdentity(
                "esploratore", "Esploratore",
                "Pugnale e mobilità per aprire il percorso.",
                ("dagger",),
            ),
            BuildIdentity(
                "rilevatore", "Rilevatore",
                "Balestra e osservazione per anticipare le imboscate.",
                ("crossbow",),
            ),
            BuildIdentity(
                "astrolabista", "Astrolabista",
                "Focus e coordinate arcane per non perdere la rotta.",
                ("focus",),
            ),
        ),
        wave="C",
    ),
    "cronista": ClassMechanic(
        "class.cronista.margine",
        "cronista",
        "Margine Vivente",
        "Il Cronista sceglie quale versione degli eventi rendere autorevole.",
        "intellect",
        ("counter_spell", "counter_curse"),
        (
            BuildIdentity(
                "archivista", "Archivista",
                "Tomo e memoria per preservare la versione corretta.",
                ("tome",),
            ),
            BuildIdentity(
                "glossatore", "Glossatore",
                "Focus e annotazioni per correggere rituali ostili.",
                ("focus",),
            ),
            BuildIdentity(
                "testimone", "Testimone Armato",
                "Pugnale e presenza per incidere la cronaca sul campo.",
                ("dagger",),
            ),
        ),
        wave="C",
    ),
    "fabbro_arcano": ClassMechanic(
        "class.fabbro_arcano.tempra",
        "fabbro_arcano",
        "Tempra Runica",
        "Il Fabbro Arcano risveglia la memoria custodita nel metallo.",
        "strength",
        ("counter_siege", "counter_magic_barrier"),
        (
            BuildIdentity(
                "forgiatore", "Forgiatore",
                "Martello e tempra per rinforzare uomini e strutture.",
                ("hammer",),
            ),
            BuildIdentity(
                "incisore", "Incisore",
                "Ascia e taglio runico per aprire armature e sigilli.",
                ("axe",),
            ),
            BuildIdentity(
                "infusore", "Infusore",
                "Focus e incantamento per trasferire potere agli item.",
                ("focus",),
            ),
        ),
        wave="C",
    ),
    "mercante": ClassMechanic(
        "class.mercante.patto",
        "mercante",
        "Patto Equo",
        "Il Mercante trasforma preparazione e fiducia in vantaggio operativo.",
        "agility",
        ("counter_ambush", "counter_stealth"),
        (
            BuildIdentity(
                "contrattatore", "Contrattatore",
                "Stocco e presenza per imporre condizioni sul campo.",
                ("rapier",),
            ),
            BuildIdentity(
                "convogliatore", "Convogliatore",
                "Balestra e logistica per proteggere uomini e merci.",
                ("crossbow",),
            ),
            BuildIdentity(
                "sensale", "Sensale d'Ombra",
                "Pugnale e contatti per scoprire accordi nascosti.",
                ("dagger",),
            ),
        ),
        wave="C",
    ),
    "runista": ClassMechanic(
        "class.runista.geometria",
        "runista",
        "Geometria Imposta",
        "Il Runista decide quale legge debba valere entro il proprio tracciato.",
        "intellect",
        ("counter_trap", "counter_magic_barrier"),
        (
            BuildIdentity(
                "tracciatore", "Tracciatore",
                "Bastone e rune d'area per controllare il terreno.",
                ("staff",),
            ),
            BuildIdentity(
                "frangisigilli", "Frangisigilli",
                "Martello e contro-rune per spezzare vincoli ostili.",
                ("hammer",),
            ),
            BuildIdentity(
                "vincolatore", "Vincolatore",
                "Focus e geometrie persistenti per imporre una legge.",
                ("focus",),
            ),
        ),
        wave="C",
    ),
}

WAVE_D_CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "astrologo": ClassMechanic(
        "class.astrologo.congiunzione",
        "astrologo",
        "Congiunzione Inevitabile",
        "L'Astrologo sceglie quale segno celeste rendere dominante.",
        "intellect",
        ("counter_spell", "counter_boss"),
        (
            BuildIdentity(
                "augure", "Augure",
                "Bastone e osservazione per preparare il gruppo.",
                ("staff",),
            ),
            BuildIdentity(
                "eclittico", "Eclittico",
                "Focus e fasi astrali per oscurare il nemico.",
                ("focus",),
            ),
            BuildIdentity(
                "efemerista", "Efemerista",
                "Tomo e calcolo per fissare il momento favorevole.",
                ("tome",),
            ),
        ),
        wave="D",
    ),
    "burattinaio": ClassMechanic(
        "class.burattinaio.filo",
        "burattinaio",
        "Tensione del Filo",
        "Il Burattinaio distribuisce controllo tra mano, filo e marionetta.",
        "agility",
        ("counter_ambush", "counter_stealth"),
        (
            BuildIdentity(
                "intagliatore", "Intagliatore",
                "Pugnale e precisione per preparare marionette aggressive.",
                ("dagger",),
            ),
            BuildIdentity(
                "ballestario", "Ballestario",
                "Balestra e fili a distanza per fermare l'imboscata.",
                ("crossbow",),
            ),
            BuildIdentity(
                "filiere", "Filiere",
                "Focus e legami invisibili per governare il campo.",
                ("focus",),
            ),
        ),
        wave="D",
    ),
    "giocatore_d_azzardo": ClassMechanic(
        "class.giocatore_d_azzardo.puntata",
        "giocatore_d_azzardo",
        "Puntata Coperta",
        "Il Giocatore d'Azzardo lega la sorte allo strumento della puntata.",
        "agility",
        ("counter_trap", "counter_curse"),
        (
            BuildIdentity(
                "baro", "Baro",
                "Pugnale e destrezza per cambiare l'esito all'ultimo.",
                ("dagger",),
            ),
            BuildIdentity(
                "croupier", "Croupier",
                "Balestra e rischio calcolato per distribuire pressione.",
                ("crossbow",),
            ),
            BuildIdentity(
                "calcolatore", "Calcolatore",
                "Focus e probabilità per limitare gli esiti peggiori.",
                ("focus",),
            ),
        ),
        wave="D",
    ),
    "parassita": ClassMechanic(
        "class.parassita.simbiosi",
        "parassita",
        "Simbiosi Affamata",
        "Il Parassita decide cosa sottrarre e quale forma farne.",
        "endurance",
        ("counter_disease", "counter_boss"),
        (
            BuildIdentity(
                "sanguisuga", "Sanguisuga",
                "Pugnale e drenaggio rapido per logorare la preda.",
                ("dagger",),
            ),
            BuildIdentity(
                "innestato", "Innestato",
                "Armi da pugno e adattamento per rubare vigore.",
                ("fist",),
            ),
            BuildIdentity(
                "mietitore", "Mietitore Simbiotico",
                "Falce e crescita parassitaria contro bersagli maggiori.",
                ("sickle",),
            ),
        ),
        wave="D",
    ),
    "pittore": ClassMechanic(
        "class.pittore.pigmento",
        "pittore",
        "Pigmento Vivente",
        "Il Pittore rende reale il tratto sostenuto dal proprio strumento.",
        "intellect",
        ("counter_stealth", "counter_magic_barrier"),
        (
            BuildIdentity(
                "miniaturista", "Miniaturista",
                "Focus e dettagli impossibili per alterare la percezione.",
                ("focus",),
            ),
            BuildIdentity(
                "affreschista", "Affreschista",
                "Bastone e immagini estese per ridisegnare il campo.",
                ("staff",),
            ),
            BuildIdentity(
                "ritrattista", "Ritrattista",
                "Pugnale e segno netto per debilitare un solo soggetto.",
                ("dagger",),
            ),
        ),
        wave="D",
    ),
    "sognatore": ClassMechanic(
        "class.sognatore.lucidita",
        "sognatore",
        "Lucidità Condivisa",
        "Il Sognatore sceglie quale presenza onirica attraversi la veglia.",
        "intellect",
        ("counter_spell", "counter_curse"),
        (
            BuildIdentity(
                "lucido", "Lucido",
                "Focus e volontà per mantenere il controllo del sogno.",
                ("focus",),
            ),
            BuildIdentity(
                "oniromante", "Oniromante",
                "Tomo e simboli per leggere le presenze oniriche.",
                ("tome",),
            ),
            BuildIdentity(
                "sonnambulo", "Sonnambulo",
                "Bastone e trance per portare il sogno sul campo.",
                ("staff",),
            ),
        ),
        wave="D",
    ),
}

WAVE_E_CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "cacciatore_del_sangue": ClassMechanic(
        "class.cacciatore_del_sangue.traccia",
        "cacciatore_del_sangue",
        "Traccia Ematica",
        "Il Cacciatore del Sangue trasforma ogni ferita in una pista.",
        "strength",
        ("counter_beast", "counter_boss"),
        (
            BuildIdentity(
                "predatore_rosso", "Predatore Rosso",
                "Ascia e pressione per ampliare le ferite aperte.",
                ("axe",),
            ),
            BuildIdentity(
                "duellante_sanguigno", "Duellante Sanguigno",
                "Spada e ritmo per sostenersi nello scontro.",
                ("sword",),
            ),
            BuildIdentity(
                "trafittore", "Trafittore",
                "Lancia e portata per inseguire la preda ferita.",
                ("spear",),
            ),
        ),
        wave="E",
    ),
    "cavaliere_della_morte": ClassMechanic(
        "class.cavaliere_della_morte.vessillo",
        "cavaliere_della_morte",
        "Vessillo Inamovibile",
        "Il Cavaliere della Morte converte memoria funebre in dominio.",
        "endurance",
        ("counter_undead", "counter_curse"),
        (
            BuildIdentity(
                "cavaliere_pallido", "Cavaliere Pallido",
                "Spada e necroenergia per avanzare senza cedere.",
                ("sword",),
            ),
            BuildIdentity(
                "boia_del_vessillo", "Boia del Vessillo",
                "Ascia e terrore per spezzare la formazione nemica.",
                ("axe",),
            ),
            BuildIdentity(
                "baluardo_nero", "Baluardo Nero",
                "Scudo e armatura per rendere la morte una difesa.",
                ("shield", "plate"),
            ),
        ),
        wave="E",
    ),
    "cavaliere_di_draghi": ClassMechanic(
        "class.cavaliere_di_draghi.patto",
        "cavaliere_di_draghi",
        "Patto delle Fiamme",
        "Il Cavaliere di Draghi accorda arma, cavalcatura e fiamma.",
        "strength",
        ("counter_elemental", "counter_siege"),
        (
            BuildIdentity(
                "lanciere_draconico", "Lanciere Draconico",
                "Lancia e slancio per spezzare il fronte.",
                ("spear",),
            ),
            BuildIdentity(
                "lama_del_drago", "Lama del Drago",
                "Spada e fiamma per sostenere l'assalto.",
                ("sword",),
            ),
            BuildIdentity(
                "custode_delle_scaglie", "Custode delle Scaglie",
                "Scudo e presenza draconica per proteggere il patto.",
                ("shield", "plate"),
            ),
        ),
        wave="E",
    ),
}

CLASS_MECHANICS: dict[str, ClassMechanic] = {
    **WAVE_A_CLASS_MECHANICS,
    **WAVE_B_CLASS_MECHANICS,
    **WAVE_C_CLASS_MECHANICS,
    **WAVE_D_CLASS_MECHANICS,
    **WAVE_E_CLASS_MECHANICS,
}

CLASS_MECHANIC_BASE_BONUS = 1
ITEM_BUILD_RESONANCE_BONUS = 2


def _equipment_tags(items: Iterable[Mapping[str, object]]) -> frozenset[str]:
    tags: set[str] = set()
    for item in items:
        for field in ("weapon_tags", "armor_tags", "tags"):
            values = item.get(field)
            if isinstance(values, (list, tuple)):
                tags.update(
                    str(value).strip().lower()
                    for value in values
                    if str(value).strip()
                )
        for field in ("weapon_type", "armor_type", "item_subtype"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                tags.add(value.strip().lower())
    return frozenset(tags)


def resolve_class_mechanic(
    *,
    adventurer: Mapping[str, object],
    equipment_items: Iterable[Mapping[str, object]] | None,
) -> dict:
    """Resolve the active class mechanic and item-selected build."""
    class_slug = str(
        adventurer.get("canonical_class_slug")
        or adventurer.get("class_slug")
        or ""
    ).strip().lower()
    mechanic = CLASS_MECHANICS.get(class_slug)
    if mechanic is None:
        return {"active": False, "power_bonus": 0, "counter_tags": []}

    equipped_tags = _equipment_tags(equipment_items or ())
    scored = [
        (len(equipped_tags.intersection(build.item_tags)), -index, build)
        for index, build in enumerate(mechanic.builds)
    ]
    score, _order, active_build = max(scored, key=lambda row: (row[0], row[1]))
    resonance = ITEM_BUILD_RESONANCE_BONUS if score > 0 else 0
    power_bonus = CLASS_MECHANIC_BASE_BONUS + resonance
    return {
        "active": True,
        "mechanic_id": mechanic.mechanic_id,
        "class_slug": mechanic.class_slug,
        "wave": mechanic.wave,
        "name_it": mechanic.name_it,
        "summary_it": mechanic.summary_it,
        "primary_stat": mechanic.primary_stat,
        "base_bonus": CLASS_MECHANIC_BASE_BONUS,
        "item_resonance_bonus": resonance,
        "power_bonus": power_bonus,
        "counter_tags": list(mechanic.counter_tags),
        "active_counter_tags": (
            list(mechanic.counter_tags) if score > 0 else []
        ),
        "equipped_tags": sorted(equipped_tags),
        "active_build": {
            "build_id": active_build.build_id,
            "name_it": active_build.name_it,
            "description_it": active_build.description_it,
            "matched_tags": sorted(
                equipped_tags.intersection(active_build.item_tags)
            ),
            "resonance_active": score > 0,
        },
        "build_options": [
            {
                "build_id": build.build_id,
                "name_it": build.name_it,
                "description_it": build.description_it,
                "item_tags": list(build.item_tags),
            }
            for build in mechanic.builds
        ],
    }


def class_mechanic_public(class_slug: str) -> dict | None:
    """Return safe design metadata for Hall choice and tester UI."""
    mechanic = CLASS_MECHANICS.get((class_slug or "").strip().lower())
    if mechanic is None:
        return None
    return {
        "mechanic_id": mechanic.mechanic_id,
        "name_it": mechanic.name_it,
        "wave": mechanic.wave,
        "summary_it": mechanic.summary_it,
        "primary_stat": mechanic.primary_stat,
        "builds": [
            {
                "build_id": build.build_id,
                "name_it": build.name_it,
                "description_it": build.description_it,
                "item_tags": list(build.item_tags),
            }
            for build in mechanic.builds
        ],
    }


def resolve_wave_a_class_mechanic(
    *,
    adventurer: Mapping[str, object],
    equipment_items: Iterable[Mapping[str, object]] | None,
) -> dict:
    """Backward-compatible alias retained for existing expedition imports."""
    return resolve_class_mechanic(
        adventurer=adventurer,
        equipment_items=equipment_items,
    )


__all__ = [
    "BuildIdentity",
    "CLASS_MECHANICS",
    "CLASS_MECHANIC_BASE_BONUS",
    "ClassMechanic",
    "ITEM_BUILD_RESONANCE_BONUS",
    "WAVE_A_CLASS_MECHANICS",
    "WAVE_B_CLASS_MECHANICS",
    "WAVE_C_CLASS_MECHANICS",
    "WAVE_D_CLASS_MECHANICS",
    "WAVE_E_CLASS_MECHANICS",
    "class_mechanic_public",
    "resolve_class_mechanic",
    "resolve_wave_a_class_mechanic",
]
