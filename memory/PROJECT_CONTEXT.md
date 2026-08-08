# Orbus Online — Project Context

**Updated:** 2026-07-30  
**Operational branch:** `main-260728`

## North Star

Orbus Online: Guild Master è un gestionale MMO fantasy. Il giocatore recluta
persone, sceglie per loro un sentiero e costruisce la Gilda soprattutto
attraverso item, collezione e lore.

```text
Recluta classless
→ Class Hall
→ prova
→ conferma
→ classe
→ item identitario
→ build
→ attività
→ nuove storie e nuovi item
```

Principi:

- 27 classi = 27 Class Hall;
- ogni avventuriero nasce Comune e senza classe;
- la rarità dell'avventuriero è anzianità di carriera, mai RNG;
- livello massimo avventuriero 80;
- dungeon 3/5/7, raid 10/15/20/40;
- equipaggiamento a dieci slot fisici;
- ogni item ha ID, slug, nome e identità singolari;
- compatibilità esplicita: riservato, consigliato o universale;
- gli effetti eseguibili risiedono nel codice statico, non nel database;
- nessuna vendita premium della potenza.

## Stato reale

- FastAPI + React + MongoDB;
- percorso classless/Hall persistente e giocabile localmente;
- 135 item Hall, cinque per classe, tutti lore-reviewed;
- 261 item attivi persistenti, tutti unici, lore-reviewed e con flavor text;
- Collection Book e item track;
- strumenti reset/smoke per tester;
- 27 classi assegnate, signature equipaggiate e provate in spedizione;
- gli effetti signature modificano il PWR e sono spiegati nel report;
- test mirati unit, real-Mongo e HTTP verdi;
- build frontend e browser QA verdi.

Il baseline non equivale ancora a 27 kit profondi e bilanciati. Restano
telemetria, encounter, build alternative, catalogo esteso e bonifica della
suite legacy.

## Contratti da non rompere

- `recruit_status=recruit_unassigned` è il marker classless autorevole;
- `class_slug=null` da solo non identifica una nuova Recluta;
- la Hall viene scelta esplicitamente dopo una prova safe-mode;
- assignment e grant sono CAS/idempotenti;
- il primo item arriva dopo, mai prima, della Hall;
- produzione è fail-closed;
- i 268 null legacy restano immutati fino a migrazione dedicata;
- i 1500 blueprint legacy non sono runtime e richiedono remap a 27 classi.

## Cacciatore del Vuoto

```text
class_id = cacciatore_del_vuoto
main stat = intellect
priority = intellect → cost → agility
fragment cap = 5
mark duration = 10 seconds
active marks = 5
combined proc = 45%
focus bonus <= 2 per resource segment
ritual-close dagger <= 1 per Mark application
```

Statistiche runtime: `strength`, `agility`, `intellect`, `endurance`, `faith`.
`cost` è una priorità di design/equip, non una sesta statistica.

## Verità e anti-drift

Ordine delle fonti:

1. codice;
2. test riproducibili e report di gate;
3. closure/manifest;
4. PRD;
5. roadmap e handoff;
6. conversazioni.

Non ricostruire un MVP da zero. Non ripristinare l’assegnazione casuale della
classe. Non dichiarare verde la suite storica senza riprodurne e bonificarne
l’ambiente. Non scrivere su database shared/prod e non distribuire senza
autorizzazione.
