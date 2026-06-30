// ROUND 15 — Fase 1 / Task 3 (rev. 15.1)
// Sezione narrativa "Classi e statistiche".
// Tutti i label statistica/ruolo sono in italiano. Il suffisso "(SLUG_EN)"
// è stato rimosso. I role label vengono mappati via `ROLE_IT`.

import { SectionBlock } from "./_shared";

// Canonical IT stat labels (used per il rendering UI, gli slug interni restano EN).
const STAT_IT = {
    strength: "Forza",
    agility: "Destrezza",
    intellect: "Intelletto",
    endurance: "Costituzione",
    faith: "Fede",
};

// Canonical IT role labels (covers role + secondary_role).
const ROLE_IT = {
    Tank: "Difensore",
    DPS: "Attaccante",
    Healer: "Guaritore",
    Caster: "Incantatore",
    Stealth: "Furtivo",
    Support: "Supporto",
    Frontline: "Prima linea",
    "Off-Healer": "Guaritore di supporto",
    "Dedicated single-target": "Cura singola dedicata",
    "AoE Heal / Hybrid Caster": "Cura ad area / Incantatore ibrido",
    "Self-Sustain": "Auto-cura",
    "Caster / Control": "Incantatore / Controllo",
    "Caster / Summoner": "Incantatore / Evocatore",
    "Scout / Ranged": "Esploratore / Distanza",
    "Burst Stealth": "Furtivo da burst",
    "Buffer / Debuffer": "Buff e debuff",
};

function roleIT(label) {
    if (!label) return "";
    return ROLE_IT[label] || label;
}

const STATS = [
    {
        slug: "strength",
        what: "La capacità grezza di colpire forte e portare carichi pesanti.",
        used_by: ["Guerriero", "Paladino", "Berserker", "Ladro (secondaria)"],
        influences: [
            "Power totale dell'avventuriero",
            "Danno con armi pesanti (spade a due mani, mazze)",
            "Equipaggiamento di tipo corazza pesante",
            "Probabilità di successo nei dungeon corpo a corpo",
        ],
        example:
            "Un Berserker con Forza 10 colpisce più duro di tutti gli altri Attaccanti fisici, ma muore in 2 turni senza Costituzione.",
    },
    {
        slug: "agility",
        what: "Velocità, riflessi e precisione nei movimenti.",
        used_by: ["Ladro", "Ranger", "Assassino", "Monaco", "Bardo (secondaria)"],
        influences: [
            "Power totale",
            "Probabilità di schivare colpi (PvP e dungeon)",
            "Iniziativa nei round combat",
            "Equipaggiamento finesse (pugnali, archi)",
        ],
        example:
            "Un Assassino con Destrezza 10 può uccidere un nemico Lv 5 senza essere colpito, ma una sola debolezza in copertura lo fa cadere.",
    },
    {
        slug: "intellect",
        what: "Acume mentale, comprensione arcana, controllo delle energie.",
        used_by: ["Mago", "Negromante", "Bardo", "Druido (secondaria)"],
        influences: [
            "Power totale",
            "Potenza degli incantesimi di danno e controllo",
            "Equipaggiamento arcano (bastoni, grimoires, sigilli)",
            "Capacità di leggere i traits più rari",
        ],
        example:
            "Un Mago con Intelletto 10 polverizza un'ondata di nemici, ma con Intelletto 5 si ritrova a lanciare scintille innocue.",
    },
    {
        slug: "endurance",
        what: "Capacità di assorbire danno e mantenere lo sforzo nel tempo.",
        used_by: ["Guerriero", "Paladino", "Berserker (secondaria)", "Ranger (secondaria)"],
        influences: [
            "Power totale",
            "Hit point effettivi nei combattimenti lunghi",
            "Equipaggiamento di tipo corazza pesante e scudi",
            "Sostenibilità nelle spedizioni multi-stadio",
        ],
        example:
            "Un Guerriero con Costituzione 9 può tenere il fronte di un raid per turni multipli; con Costituzione 3 sarebbe fuori al primo colpo.",
    },
    {
        slug: "faith",
        what: "Connessione con il sacro, fonte di guarigione e luce.",
        used_by: ["Sacerdote", "Druido", "Paladino"],
        influences: [
            "Power totale",
            "Potenza delle cure e degli incantesimi sacri",
            "Equipaggiamento sacro (reliquie, sceptri, talismani)",
            "Resistenza a effetti negativi di tipo \"oscuro/non-morto\"",
        ],
        example:
            "Un Sacerdote con Fede 10 può salvare un avventuriero sull'orlo della morte in un raid; con Fede 3 può solo accelerare un riposo.",
    },
];

// CLASSES uses canonical IT stat labels (Forza/Destrezza/Intelletto/Costituzione/Fede).
const CLASSES = [
    { slug: "warrior", name_it: "Guerriero", role: "Tank", secondary_role: "Frontline",
        primary_stat: "Forza", secondary_stats: ["Costituzione"],
        equip: "Spade e asce a una o due mani, mazze, scudi pesanti, corazze a piastre. Mai armatura di stoffa.",
        playstyle: "Si piazza davanti al party, intercetta i colpi e li restituisce. Lento ma inossidabile.",
        differs_from: "Diversamente dal Paladino, non sa curare. Diversamente dal Berserker, non scambia la difesa per più danno.",
        strengths: ["Sopravvivenza altissima", "Aggro stabile", "Equipaggiamento abbondante"],
        weaknesses: ["Lento", "Nessun danno magico", "Niente cure"],
        good_in: ["Dungeon Tier 1-3 con boss melee", "Spedizioni lunghe con pochi guaritori"] },

    { slug: "paladin", name_it: "Paladino", role: "Tank", secondary_role: "Off-Healer",
        primary_stat: "Fede", secondary_stats: ["Forza", "Costituzione"],
        equip: "Spade/mazze sacre, scudi, armatura pesante con simboli sacri. Reliquie e talismani.",
        playstyle: "Difensore ibrido: meno duro del Guerriero puro, ma può curare l'alleato accanto e colpire più forte i nemici non-morti.",
        differs_from: "Il Guerriero è più resistente; il Sacerdote cura di più. Il Paladino unisce le due cose a metà costo.",
        strengths: ["Versatilità", "Auto-sostegno", "Bonus vs Vuoto/Non-morti"],
        weaknesses: ["Né il miglior difensore né il miglior guaritore", "Statistiche spalmate"],
        good_in: ["Raid lunghi", "Dungeon di tipo Vuoto/Non-morti", "Squadre con un solo guaritore"] },

    { slug: "rogue", name_it: "Ladro", role: "DPS", secondary_role: "Stealth",
        primary_stat: "Destrezza", secondary_stats: ["Forza"],
        equip: "Pugnali, spade corte, armi finesse. Armatura leggera in cuoio. Niente piastre.",
        playstyle: "Si infila tra le linee, colpisce il bersaglio più vulnerabile, sparisce. Critici frequenti.",
        differs_from: "L'Assassino è più letale in singolo colpo ma meno sostenibile; il Ranger lavora a distanza.",
        strengths: ["Danno alto su bersagli isolati", "Iniziativa", "Mobilità"],
        weaknesses: ["Fragile", "Vulnerabile a controllo di gruppo"],
        good_in: ["Dungeon con boss singolo", "PvP veloce"] },

    { slug: "ranger", name_it: "Ranger", role: "DPS", secondary_role: "Scout / Ranged",
        primary_stat: "Destrezza", secondary_stats: ["Costituzione"],
        equip: "Archi, balestre, frecce stregate. Armatura leggera/media. Lavora a distanza.",
        playstyle: "Mantiene la distanza, colpisce prima che il nemico si avvicini. Esploratore naturale.",
        differs_from: "Il Ladro lavora a corto raggio; il Ranger usa la stessa stat ma per il tiro lungo. La Costituzione secondaria gli permette spedizioni più lunghe.",
        strengths: ["Danno costante", "Sicurezza dalla distanza", "Buono nelle esplorazioni"],
        weaknesses: ["Soffre in stanze strette", "Munizioni/consumabili da gestire"],
        good_in: ["Dungeon all'aperto", "Spedizioni esplorative", "Raid contro boss volanti"] },

    { slug: "assassin", name_it: "Assassino (specializzazione di Ladro)", is_specialization: true, parent_class_it: "Ladro", role: "DPS", secondary_role: "Burst Stealth",
        primary_stat: "Destrezza", secondary_stats: ["Forza"],
        equip: "Pugnali avvelenati, armi finesse. Armatura quasi nulla, abito d'ombra.",
        playstyle: "Aspetta. Colpisce. Sparisce. Un solo colpo, idealmente decisivo.",
        differs_from: "Il Ladro è più sostenibile e versatile; l'Assassino è chirurgico. Crolla appena viene visto.",
        strengths: ["Burst damage estremo", "Furtività pura", "Critici alti"],
        weaknesses: ["Estremamente fragile", "Pessimo se scoperto", "Niente sostegno"],
        good_in: ["Boss con poco HP da chiudere rapidamente", "PvP one-shot"] },

    { slug: "berserker", name_it: "Berserker (specializzazione di Guerriero)", is_specialization: true, parent_class_it: "Guerriero", role: "DPS", secondary_role: "Frontline",
        primary_stat: "Forza", secondary_stats: ["Costituzione"],
        equip: "Armi a due mani: asce, claymore, martelli. Armatura media — niente scudo per definizione.",
        playstyle: "Carica frontalmente, colpisce a piena forza. Più la sua salute scende, più colpisce.",
        differs_from: "Il Guerriero difende e regge i colpi; il Berserker assorbe e li restituisce molto più forte ma muore prima.",
        strengths: ["Danno corpo a corpo top-tier", "Resilienza media", "Identità chiara"],
        weaknesses: ["Niente cure", "Niente difesa attiva", "Squilibrato in raid lunghi"],
        good_in: ["Dungeon fast clear", "Boss melee tankato da un alleato"] },

    { slug: "monk", name_it: "Monaco", role: "DPS", secondary_role: "Self-Sustain",
        primary_stat: "Destrezza", secondary_stats: ["Costituzione", "Fede"],
        equip: "Armi nude o bastoni. Mai armatura pesante: la sua difesa è l'evasione.",
        playstyle: "Schiva, colpisce a mani nude o con bastone, recupera piccole ferite tra una mossa e l'altra.",
        differs_from: "Il Ladro è più burst, l'Assassino più letale; il Monaco si bilancia tra danno e autosostegno.",
        strengths: ["Auto-cura leggera", "Mobilità", "Indipendente dall'equip"],
        weaknesses: ["Equip limitato", "Picchi di danno minori degli Attaccanti puri"],
        good_in: ["Spedizioni solo-friendly", "Dungeon con poche cure disponibili"] },

    { slug: "mage", name_it: "Mago", role: "DPS", secondary_role: "Caster / Control",
        primary_stat: "Intelletto", secondary_stats: ["Costituzione"],
        equip: "Bastoni arcani, bacchette, grimoires. Armatura in stoffa, mai pesante.",
        playstyle: "Sceglie l'incantesimo giusto, lo lancia, ripete. Versatile su danno e controllo.",
        differs_from: "Il Negromante usa la stessa stat ma con flavor oscuro; il Druido cura più di quanto colpisce.",
        strengths: ["Ventaglio di incantesimi", "AoE", "Controllo del campo"],
        weaknesses: ["Fragile", "Dipende dal mana / cooldown", "Vulnerabile in melee"],
        good_in: ["Dungeon con ondate", "Boss con meccaniche complesse", "AoE clear"] },

    { slug: "necromancer", name_it: "Negromante (specializzazione di Mago)", is_specialization: true, parent_class_it: "Mago", role: "DPS", secondary_role: "Caster / Summoner",
        primary_stat: "Intelletto", secondary_stats: ["Destrezza"],
        equip: "Bastoni d'ossa, falci, simboli oscuri. Vesti rituali, mai armatura forte.",
        playstyle: "Drena vita, evoca scheletri, decompone i bersagli. Lavora di logoramento.",
        differs_from: "Il Mago crea fiamme; il Negromante crea servitori. Il Mago controlla l'arcano; il Negromante controlla la morte.",
        strengths: ["Damage over time", "Servitori evocati", "Sinergie con loot non-morto"],
        weaknesses: ["Setup lento", "Disprezzato in spedizioni \"sacre\""],
        good_in: ["Dungeon non-morti (sinergie loot)", "Spedizioni lunghe dove i pet aiutano"] },

    { slug: "priest", name_it: "Sacerdote", role: "Healer", secondary_role: "Dedicated single-target",
        primary_stat: "Fede", secondary_stats: ["Intelletto"],
        equip: "Mazze sacre, scettri, libri di preghiera. Vesti, talismani sacri.",
        playstyle: "Tiene in piedi il bersaglio più importante. Cura singola enorme, cura di gruppo limitata.",
        differs_from: "Il Druido cura più alleati insieme (AoE); il Sacerdote è il salvavita del singolo Difensore.",
        strengths: ["Cura singola top-tier", "Buff anti-morte", "Identità chiara"],
        weaknesses: ["Niente AoE heal", "Niente danno reale"],
        good_in: ["Raid con un solo difensore da tenere su", "Dungeon hard mode con boss melee"] },

    { slug: "druid", name_it: "Druido", role: "Healer", secondary_role: "AoE Heal / Hybrid Caster",
        primary_stat: "Fede", secondary_stats: ["Intelletto"],
        equip: "Bastoni naturali, clave rituali, vesti in cuoio o stoffa naturale.",
        playstyle: "Cura più alleati insieme, lancia incantesimi naturali, si adatta. Meno specialista ma più flessibile.",
        differs_from: "Il Sacerdote è migliore sul singolo target; il Druido brilla quando tre alleati sono feriti contemporaneamente.",
        strengths: ["AoE heal", "Flessibilità", "Danno secondario reale"],
        weaknesses: ["Cura singola inferiore al Sacerdote", "Identità ibrida non sempre apprezzata"],
        good_in: ["Dungeon a 5 con molti danni AoE", "Spedizioni con squadra ferita diffusamente"] },

    { slug: "bard", name_it: "Bardo", role: "Support", secondary_role: "Buffer / Debuffer",
        primary_stat: "Intelletto", secondary_stats: ["Destrezza", "Fede"],
        equip: "Pugnali e strumenti musicali. Armatura leggera per restare mobile.",
        playstyle: "Non fa il danno più alto né cura più di tutti, ma migliora chi ha attorno. Nemici stonati, alleati ispirati.",
        differs_from: "L'unica classe Supporto pura. Il suo valore non è nel suo colpo, ma nel moltiplicatore che dà agli altri.",
        strengths: ["Buff costanti", "Debuff sui nemici", "Utility uniche"],
        weaknesses: ["Danno solo basso", "Inutile in 1v1 PvP"],
        good_in: ["Raid", "Squadre da 5+ a basso power"] },

    // ROUND 16.0.1 — 11th base class.
    { slug: "alchemist", name_it: "Alchimista", role: "DPS", secondary_role: "Support",
        primary_stat: "Intelletto", secondary_stats: ["Destrezza", "Costituzione"],
        equip: "Pugnali, tomi, fiale alchemiche. Armature leggere o vesti.",
        playstyle: "Lancia bombe, distilla veleni, prepara elisir. Studioso pragmatico, sfrutta la chimica più che la magia pura.",
        differs_from: "Mentre il Mago piega l'arcano e il Negromante (specializzazione del Mago) anima i morti, l'Alchimista è uno sperimentatore terreno: trasforma materia ed essenze in armi e cure.",
        strengths: ["AoE esplosivo (Bombardiere)", "DoT veleni (Tossicologo)", "Counter maledizioni e barriere (Trasmutatore)"],
        weaknesses: ["HP medi", "Difesa fisica scarsa", "Dipende dai materiali alchemici"],
        good_in: ["Dungeon con boss avvelenabili", "Spedizioni assedio", "Squadre con ferite/maledizioni da curare"] },
];

const PRIMARY_STAT_WARNING = (
    <p
        data-testid="guide-class-warning-15-2"
        className="text-[12px] text-amber/95 border-l-2 border-amber pl-3 italic mt-3"
    >
        <strong className="text-amber not-italic">Attivo (Round 15.2):</strong>{" "}
        se la statistica primaria della classe scende sotto la soglia attesa
        per il livello attuale, l&apos;XP guadagnato in spedizione si riduce:
        −10% (soglia minore), −20% (soglia maggiore), fino a −30% (critica).
        Mai sotto il 70%.
    </p>
);

function StatEntry({ stat }) {
    return (
        <article
            data-testid={`guide-stat-${stat.slug}`}
            className="border-l-2 border-amber/40 pl-4 mb-5"
        >
            <h3 className="text-[15px] text-foreground font-semibold mb-1">
                {STAT_IT[stat.slug] || stat.slug}
            </h3>
            <p className="text-[12px] text-muted-foreground mb-2">{stat.what}</p>
            <p className="text-[12px]">
                <strong className="text-amber/90">Chi la usa meglio:</strong>{" "}
                {stat.used_by.join(", ")}.
            </p>
            <p className="text-[12px] mt-1.5"><strong className="text-amber/90">Cosa influenza:</strong></p>
            <ul className="text-[12px] list-disc list-inside ml-1 mt-1 text-muted-foreground/95">
                {stat.influences.map((line) => <li key={line}>{line}</li>)}
            </ul>
            <p className="text-[12px] mt-2 italic text-foreground/80">
                <strong className="not-italic text-amber/80">Esempio.</strong> {stat.example}
            </p>
        </article>
    );
}

function ClassEntry({ cls }) {
    const rolesIT = [roleIT(cls.role), cls.secondary_role ? roleIT(cls.secondary_role) : null]
        .filter(Boolean).join(" · ");
    return (
        <article
            data-testid={`guide-class-${cls.slug}`}
            className="border border-border bg-background/30 rounded-sm p-4 mb-4"
        >
            <header className="flex items-baseline justify-between gap-3 mb-2 flex-wrap">
                <h3 className="text-[15px] text-foreground font-semibold">
                    {cls.name_it}
                    {cls.is_specialization && (
                        <span className="ml-2 text-[10px] tracking-widest text-amber/90 border border-amber/50 rounded-sm px-2 py-0.5 align-middle">
                            SPEC
                        </span>
                    )}
                </h3>
                <span
                    data-testid={`guide-class-${cls.slug}-roles`}
                    className="text-[10px] text-amber tracking-widest"
                >
                    {rolesIT}
                </span>
            </header>

            <dl className="text-[12px] grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 mb-3">
                <div>
                    <dt className="inline text-muted-foreground">Statistica primaria: </dt>
                    <dd className="inline text-amber">{cls.primary_stat}</dd>
                </div>
                <div>
                    <dt className="inline text-muted-foreground">Secondarie utili: </dt>
                    <dd className="inline">{cls.secondary_stats.join(", ")}</dd>
                </div>
            </dl>

            <p className="text-[12px] mb-2">
                <strong className="text-amber/90">Equipaggiamento consigliato.</strong>{" "}
                {cls.equip}
            </p>
            <p className="text-[12px] mb-2">
                <strong className="text-amber/90">Stile di gioco.</strong>{" "}
                {cls.playstyle}
            </p>
            <p className="text-[12px] mb-2">
                <strong className="text-amber/90">Differenze.</strong>{" "}
                {cls.differs_from}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-[12px] mb-2">
                <div>
                    <strong className="text-emerald-400/95">Punti forti.</strong>{" "}
                    {cls.strengths.join(", ")}.
                </div>
                <div>
                    <strong className="text-red-400/90">Punti deboli.</strong>{" "}
                    {cls.weaknesses.join(", ")}.
                </div>
            </div>

            <p className="text-[12px] text-muted-foreground/95">
                <strong className="text-amber/80">Brilla in:</strong>{" "}
                {cls.good_in.join("; ")}.
            </p>

            {PRIMARY_STAT_WARNING}
        </article>
    );
}

export default function ClassesAndStatsSection() {
    return (
        <SectionBlock id="classi-e-stats" title="Classi e statistiche">
            <p className="text-[13px] mb-4">
                Ogni avventuriero ha cinque statistiche fondamentali — Forza,
                Destrezza, Intelletto, Costituzione, Fede — e una classe che
                gli dice quale di queste è la più importante. Capire questa
                coppia è la differenza fra una squadra di mercenari assemblata
                a caso e un party che vince un raid.
            </p>

            <h3 className="text-[13px] text-amber tracking-widest mb-3 mt-6">
                :: STATISTICHE
            </h3>
            {STATS.map((s) => <StatEntry key={s.slug} stat={s} />)}

            <h3 className="text-[13px] text-amber tracking-widest mb-3 mt-8">
                :: CLASSI
            </h3>
            <p className="text-[12px] text-muted-foreground mb-4">
                Undici classi base attive nel gioco (Guerriero, Paladino, Ladro,
                Ranger, Monaco, Mago, Sacerdote, Druido, Bardo, Stregone, Alchimista)
                più tre specializzazioni storiche iconiche (Assassino, Berserker,
                Negromante), che dal Round 16.0 sono passate da classi base a
                specializzazioni delle rispettive sale di classe.
                Ognuna è progettata per fare bene una cosa specifica: il tuo
                lavoro come Guild Master è scegliere chi mandare a fare cosa.
            </p>
            {CLASSES.map((c) => <ClassEntry key={c.slug} cls={c} />)}
        </SectionBlock>
    );
}
