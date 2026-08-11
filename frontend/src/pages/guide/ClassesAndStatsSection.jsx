// FASE 9 — Sezione Guida "Classi e statistiche" riscritta sul nuovo
// Source of Truth: 27 CLASSI, ognuna con un RUOLO FISSO
// (13 Danno · 6 Difensori · 8 Guaritori). Niente specializzazioni,
// niente build: la classe È l'identità. I dati rispecchiano il registry
// canonico del server (backend/app/classes/registry.py).

import { SectionBlock } from "./_shared";

const STAT_IT = {
    strength: "Forza",
    agility: "Destrezza",
    intellect: "Intelletto",
    endurance: "Costituzione",
    faith: "Fede",
};

const ROLE_META = {
    DPS: {
        label: "Danno (DPS)",
        color: "text-red-300",
        border: "border-red-400/40",
        blurb: (
            "13 classi. Il loro compito è abbattere la minaccia: l'equip " +
            "e i set raid rafforzano la statistica primaria della classe."
        ),
    },
    TANK: {
        label: "Difensore (Tank)",
        color: "text-sky-300",
        border: "border-sky-400/40",
        blurb: (
            "6 classi. Reggono il fronte e assorbono i colpi: l'equip e i " +
            "set raid rafforzano prima di tutto la Costituzione."
        ),
    },
    HEALER: {
        label: "Guaritore (Healer)",
        color: "text-emerald-300",
        border: "border-emerald-400/40",
        blurb: (
            "8 classi. Tengono in piedi la compagnia: l'equip e i set " +
            "raid rafforzano prima di tutto la Fede."
        ),
    },
};

// 27 classi canoniche — stessi contenuti del registry server.
const CLASSES = [
    { slug: "guerriero", name: "Guerriero", role: "DPS", stat: "strength",
      identity: "L'acciaio non si spezza. Si tempra.",
      style: "Maestro d'armi in prima linea: pressione costante e colpi pesanti." },
    { slug: "ladro", name: "Ladro", role: "DPS", stat: "agility",
      identity: "Un passo taciuto vale più di cento minacce.",
      style: "Assalti dall'ombra: aperture rapide, critici ed elusione." },
    { slug: "mago", name: "Mago", role: "DPS", stat: "intellect",
      identity: "Ogni sigillo custodisce una domanda più pericolosa della risposta.",
      style: "Incantatore puro: esplosioni arcane e controllo del campo." },
    { slug: "monaco", name: "Monaco", role: "DPS", stat: "agility",
      identity: "Il corpo è la prima disciplina.",
      style: "Combo senz'armi, mobilità e recupero tramite disciplina." },
    { slug: "negromante", name: "Negromante", role: "DPS", stat: "intellect",
      identity: "Ciò che è finito continua se sa il proprio nome.",
      style: "Necroenergia e servitori non morti che logorano il nemico." },
    { slug: "cacciatore_del_vuoto", name: "Cacciatore del Vuoto", role: "DPS", stat: "intellect",
      identity: "Si caccia ciò che non ha peso.",
      style: "Tiro a lunga distanza: l'unica lama che morde gli incorporei." },
    { slug: "artificiere", name: "Artificiere", role: "DPS", stat: "agility",
      identity: "Ciò che si rompe si rifà; ciò che si rifà migliora.",
      style: "Torrette e ordigni: danno meccanico che non conosce stanchezza." },
    { slug: "cartografo", name: "Cartografo", role: "DPS", stat: "agility",
      identity: "La mappa non descrive, la mappa ricorda.",
      style: "Colpi di precisione dove la mappa dice che il nemico sarà." },
    { slug: "runista", name: "Runista", role: "DPS", stat: "intellect",
      identity: "La runa non descrive, la runa impone.",
      style: "Rune incise che detonano ad area: il danno è già scritto." },
    { slug: "burattinaio", name: "Burattinaio", role: "DPS", stat: "agility",
      identity: "Il filo che tiene è il filo che libera.",
      style: "Marionette da guerra manovrate a distanza da fili invisibili." },
    { slug: "giocatore_d_azzardo", name: "Giocatore d'Azzardo", role: "DPS", stat: "agility",
      identity: "La sorte è un patto scritto in nero.",
      style: "Rischio calcolato: colpi che possono raddoppiare." },
    { slug: "pittore", name: "Pittore", role: "DPS", stat: "intellect",
      identity: "Il colore giusto costa.",
      style: "Immagini viventi e ritratti debilitanti che feriscono davvero." },
    { slug: "cacciatore_del_sangue", name: "Cacciatore del Sangue", role: "DPS", stat: "strength",
      identity: "Il sangue sa dove torna.",
      style: "Emorragia e inseguimento: più la preda è ferita, più affonda." },
    { slug: "paladino", name: "Paladino", role: "TANK", stat: "faith",
      identity: "La luce resta quando il voto costa più della vittoria.",
      style: "Baluardo consacrato: attira i colpi e li restituisce come giudizio." },
    { slug: "cacciatore_di_mostri", name: "Cacciatore di Mostri", role: "TANK", stat: "endurance",
      identity: "La pista parla soltanto a chi smette di inseguire il rumore.",
      style: "Aggancia la preda, la trattiene e ne assorbe la furia." },
    { slug: "fabbro_arcano", name: "Fabbro Arcano", role: "TANK", stat: "strength",
      identity: "Il metallo tace ma ricorda.",
      style: "Corazza runica autoriparante: ogni colpo subito incide protezione." },
    { slug: "parassita", name: "Parassita", role: "TANK", stat: "endurance",
      identity: "Si vive di ciò che si trova.",
      style: "Drena vigore dai nemici: più viene colpito, più radica e resiste." },
    { slug: "cavaliere_della_morte", name: "Cavaliere della Morte", role: "TANK", stat: "endurance",
      identity: "La morte è già passata, io la seguo.",
      style: "Tenuta oltre la vita: vessillo nero e aura di paura." },
    { slug: "cavaliere_di_draghi", name: "Cavaliere di Draghi", role: "TANK", stat: "strength",
      identity: "Il drago non si comanda, si accompagna.",
      style: "Avanguardia in scaglie di drago: carica e fiamma che tiene il fronte." },
    { slug: "alchimista", name: "Alchimista", role: "HEALER", stat: "intellect",
      identity: "Un grammo separa cura e veleno.",
      style: "Pozioni e distillati: cura misurata al grammo, antidoti per tutto." },
    { slug: "bardo", name: "Bardo", role: "HEALER", stat: "faith",
      identity: "Una canzone rimasta a metà è un patto.",
      style: "Armonie che ricuciono: il morale è la prima medicina." },
    { slug: "druido", name: "Druido", role: "HEALER", stat: "faith",
      identity: "La foresta chiede prima di dare.",
      style: "Guarigione naturale: linfa, rigenerazione e pazienza millenaria." },
    { slug: "sciamano", name: "Sciamano", role: "HEALER", stat: "faith",
      identity: "Lo spirito non parla, lo spirito ricorda.",
      style: "Cura elementale e totem: gli spiriti sostengono chi il tamburo chiama." },
    { slug: "cronista", name: "Cronista", role: "HEALER", stat: "intellect",
      identity: "Ciò che viene scritto oggi accade oggi per sempre.",
      style: "Riscrive le ferite come refusi: ciò che la penna corregge, il corpo dimentica." },
    { slug: "mercante", name: "Mercante", role: "HEALER", stat: "agility",
      identity: "Il prezzo giusto è quello che entrambi accettano.",
      style: "Rifornimenti e contratti di soccorso: nessuna ferita resta aperta." },
    { slug: "astrologo", name: "Astrologo", role: "HEALER", stat: "intellect",
      identity: "Ciò che è scritto in alto è già accaduto in basso.",
      style: "Legge le ferite prima che accadano: destini raddrizzati." },
    { slug: "sognatore", name: "Sognatore", role: "HEALER", stat: "intellect",
      identity: "Il sogno è già accaduto, solo non lo sappiamo.",
      style: "Ripara nel sogno ciò che il giorno ha rotto." },
];

const STATS = [
    { slug: "strength",
      what: "La capacità grezza di colpire forte e portare carichi pesanti.",
      note: "Stat primaria di Guerriero, Cacciatore del Sangue, Fabbro Arcano e Cavaliere di Draghi." },
    { slug: "agility",
      what: "Velocità, riflessi e precisione nei movimenti.",
      note: "Stat primaria di Ladro, Monaco, Artificiere, Cartografo, Burattinaio, Giocatore d'Azzardo e Mercante." },
    { slug: "intellect",
      what: "Acume mentale, comprensione arcana, controllo delle energie.",
      note: "Stat primaria di Mago, Negromante, Runista, Pittore, Alchimista, Cronista, Astrologo, Sognatore e Cacciatore del Vuoto." },
    { slug: "endurance",
      what: "Capacità di assorbire danno e mantenere lo sforzo nel tempo.",
      note: "Stat primaria di Cacciatore di Mostri, Parassita e Cavaliere della Morte. È il focus dell'equip di TUTTI i Difensori." },
    { slug: "faith",
      what: "Connessione con il sacro, fonte di guarigione e luce.",
      note: "Stat primaria di Paladino, Bardo, Druido e Sciamano. È il focus dell'equip di TUTTI i Guaritori." },
];

export default function ClassesAndStatsSection() {
    return (
        <SectionBlock
            id="classi-e-statistiche"
            title="Classi e statistiche — 27 classi, ruolo fisso"
        >
            <div className="space-y-4 text-sm leading-relaxed">
                <p>
                    Ogni avventuriero nasce <strong>senza classe</strong>; nella{" "}
                    <strong>Sala di Classe</strong> supera la prova e giura a una
                    delle <strong>27 classi canoniche</strong>. La classe determina
                    TUTTO: il <strong>ruolo fisso</strong> (Danno, Difensore o
                    Guaritore), l&apos;equipaggiamento che può indossare, la meccanica
                    di combattimento e i <strong>4 set raid</strong> dedicati.
                    Non esistono specializzazioni da scegliere né build da attivare:
                    se vuoi un ruolo diverso, scegli una classe diversa.
                </p>

                <div className="border border-border rounded-sm p-3 bg-card/50">
                    <div className="text-[10px] tracking-widest text-amber mb-1">
                        :: LA CATENA CANONICA
                    </div>
                    <p className="font-mono text-xs">
                        AVVENTURIERO → CLASSE → RUOLO FISSO → EQUIP DI CLASSE → SET RAID
                    </p>
                </div>

                {Object.entries(ROLE_META).map(([role, meta]) => (
                    <section key={role}>
                        <h4 className={`text-sm font-bold tracking-widest ${meta.color} mb-1`}>
                            :: {meta.label.toUpperCase()} —{" "}
                            {CLASSES.filter((c) => c.role === role).length} CLASSI
                        </h4>
                        <p className="text-xs text-muted-foreground mb-2">{meta.blurb}</p>
                        <div className="space-y-2">
                            {CLASSES.filter((c) => c.role === role).map((c) => (
                                <div
                                    key={c.slug}
                                    className={`border ${meta.border} rounded-sm p-3 bg-card/40`}
                                >
                                    <div className="flex items-baseline justify-between gap-2 flex-wrap">
                                        <span className="font-semibold">{c.name}</span>
                                        <span className="text-[10px] text-muted-foreground">
                                            Stat primaria: {STAT_IT[c.stat]}
                                        </span>
                                    </div>
                                    <p className="text-[11px] text-amber/80 italic mt-0.5">
                                        “{c.identity}”
                                    </p>
                                    <p className="text-xs text-foreground/85 mt-1">{c.style}</p>
                                </div>
                            ))}
                        </div>
                    </section>
                ))}

                <section>
                    <h4 className="text-sm font-bold tracking-widest text-amber mb-2">
                        :: LE 5 STATISTICHE
                    </h4>
                    <div className="space-y-2">
                        {STATS.map((s) => (
                            <div key={s.slug} className="border border-border rounded-sm p-3 bg-card/40">
                                <div className="font-semibold text-sm">{STAT_IT[s.slug]}</div>
                                <p className="text-xs text-foreground/85 mt-0.5">{s.what}</p>
                                <p className="text-[11px] text-muted-foreground mt-1">{s.note}</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                        Tutte e cinque le statistiche sommano nel Potere (PWR)
                        dell&apos;avventuriero, insieme a livello, rarità di carriera,
                        equipaggiamento e bonus dei set raid.
                    </p>
                </section>
            </div>
        </SectionBlock>
    );
}
